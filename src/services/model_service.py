import io

from pathlib import Path
import numpy as np
import onnxruntime as ort
from PIL import Image
from typing import List, Tuple

from src.schemes.PredictionResult import PredictionResult

# Base path to locate model file reliably
BASE_DIR = Path(__file__).resolve().parent.parent



class AnimalModelService:

    # ImageNet normalization parameters
    MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    def __init__(self):
        # 1. Get directory containing model_service.py (src/services)
        service_dir = Path(__file__).resolve().parent

        # 2. Get the src directory (src/services -> src)
        src_dir = service_dir.parent

        # 3. Path to src/models/
        self.model_path = src_dir / "models" / "resnet101.onnx"
        self.labels_path = src_dir / "models" / "imagenet_classes.txt"

        self._init_service()

    def _init_service(self) -> None:
        """Initializes the ONNX Runtime InferenceSession and loads ImageNet labels."""
        print("Initializing ONNX Runtime Environment...")

        model_file = Path(self.model_path)
        if not model_file.exists():
            raise FileNotFoundError(
                f"ONNX model file not found at: {self.model_path}"
            )

        # 1. Initialize ONNX Session with options
        options = ort.SessionOptions()
        options.enable_cpu_mem_arena = False  # Forces release back to OS heap more aggressively
        options.graph_optimization_level = (
            ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        )

        self.session = ort.InferenceSession(
            str(model_file.resolve()),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )
        print("ONNX ResNet-101 session initialized successfully!")

        # 2. Load ImageNet Labels
        labels_file = Path(self.labels_path)
        if labels_file.exists():
            with open(labels_file, "r", encoding="utf-8") as f:
                self.labels = [line.strip() for line in f.readlines()]
            print(f"Loaded {len(self.labels)} ImageNet labels.")
        else:
            print(
                f"Warning: Labels file not found at {self.labels_path}. Fallback to numeric IDs."
            )

    def classify_image(
            self, image_bytes: bytes, top_k: int = 5
    ) -> List[PredictionResult]:
        """Accepts image bytes, preprocesses, runs ONNX inference, and returns top-K predictions."""
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise ValueError("Invalid or unsupported image file") from e

        # Preprocess -> NCHW Float32 Buffer
        input_tensor = self._preprocess_image(image)

        # Run ONNX Inference
        logits = self._run_inference(input_tensor)

        # Postprocess Logits -> Top-K Predictions
        return self._get_top_k_predictions(logits, top_k)

    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """Resizes shortest edge to 256px, center crops to 224x224, and normalizes to NCHW."""
        width, height = image.size

        # Step 1: Scale shortest side to 256px while preserving aspect ratio
        if width < height:
            target_width = 256
            target_height = int((height / width) * 256)
        else:
            target_height = 256
            target_width = int((width / height) * 256)

        resized_image = image.resize(
            (target_width, target_height), Image.Resampling.BILINEAR
        )

        # Step 2: Center crop 224x224
        left = (target_width - 224) // 2
        top = (target_height - 224) // 2
        right = left + 224
        bottom = top + 224
        cropped_image = resized_image.crop((left, top, right, bottom))

        # Step 3: Convert PIL Image to NumPy array (HWC -> [0.0, 1.0])
        img_np = np.array(cropped_image, dtype=np.float32) / 255.0

        # Step 4: Apply ImageNet Normalization (val - mean) / std
        normalized_img = (img_np - self.MEAN) / self.STD

        # Step 5: Convert HWC (224, 224, 3) to NCHW (1, 3, 224, 224)
        nchw_tensor = np.transpose(normalized_img, (2, 0, 1))
        nchw_tensor = np.expand_dims(nchw_tensor, axis=0)

        return nchw_tensor

    def _run_inference(self, input_tensor: np.ndarray) -> np.ndarray:
        """Executes a forward pass through the ONNX ResNet model."""
        input_name = self.session.get_inputs()[0].name
        output_name = self.session.get_outputs()[0].name

        # Run model inference
        results = self.session.run([output_name], {input_name: input_tensor})
        return results[0][0]  # Extract 1D array of logits (size 1000)

    def _get_top_k_predictions(
            self, logits: np.ndarray, k: int
    ) -> List[PredictionResult]:
        """Calculates Softmax and extracts the Top-K predicted classes."""
        probs = self._softmax(logits)

        # Get indices of top-K highest probabilities in descending order
        top_k_indices = np.argsort(probs)[-k:][::-1]

        results = []
        for class_id in top_k_indices:
            prob = float(probs[class_id])
            label = (
                self.labels[class_id]
                if class_id < len(self.labels)
                else "Unknown Class"
            )
            formatted_prob = f"{prob * 100:.2f}%"

            results.append(
                PredictionResult(
                    class_id=int(class_id),
                    label=label,
                    probability=formatted_prob,
                )
            )

        return results

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        """Computes numerically stable Softmax over raw logits."""
        max_logit = np.max(logits)
        exp_logits = np.exp(logits - max_logit)  # Subtract max for stability
        return exp_logits / np.sum(exp_logits)

    def predict(self, feature_vector: list[float]) -> dict:
        """Runs inference on a list of numerical features."""
        # Convert incoming python list to a 2D float32 NumPy array
        # Shape: (1, 128) matching model input
        input_data = np.array([feature_vector], dtype=np.float32)

        # Run model inference
        outputs = self.session.run(
            [self.output_name], {self.input_name: input_data}
        )
        raw_scores = outputs[0][0]

        # Get predicted class index (highest score)
        predicted_class_id = int(np.argmax(raw_scores))
        predicted_label = self.labels.get(predicted_class_id, "Unknown")

        return {
            "prediction": predicted_label,
            "class_id": predicted_class_id,
            "raw_scores": raw_scores.tolist(),
        }


# Global singleton instance
onnx_service = AnimalModelService()