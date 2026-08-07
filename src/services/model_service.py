import io

from pathlib import Path
from typing import TextIO, Union, BinaryIO
import json
import numpy as np
import onnxruntime as ort
from fastapi import UploadFile
from PIL import Image


# Base path to locate model file reliably
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "animal_model.onnx"


class AnimalModelService:

    def __init__(self):
        # 1. Start the ONNX Runtime session
        self.session = ort.InferenceSession(str(MODEL_PATH))

        # 2. Cache input & output layer names
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

        # Label map corresponding to your output indices (0, 1, 2)
        self.labels = {0: "Cat", 1: "Dog", 2: "Bird"}

    async def predictWithFile(
            self, file: Union[UploadFile, TextIO, BinaryIO, bytes, str]
    ) -> dict:
        """Safely extracts text/data whether given an UploadFile, file handle, or raw bytes."""

        if isinstance(file, UploadFile):
            bytes_content = await file.read()
            text_content = bytes_content.decode("utf-8")
        elif isinstance(file, bytes):
            # ✅ FIX: 'file' is already bytes, DO NOT call file.read()
            text_content = file.decode("utf-8")
        elif isinstance(file, str):
            text_content = file
        elif hasattr(file, "read"):
            # File object / handle (e.g., open file or BytesIO)
            content = file.read()
            text_content = (
                content.decode("utf-8") if isinstance(content, bytes) else content
            )
        else:
            raise ValueError(f"Unsupported input type: {type(file)}")

        # Parse JSON
        data = json.loads(text_content)
        return self.predict(data["features"])

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