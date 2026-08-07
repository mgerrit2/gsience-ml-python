import logging
import shutil
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile, status, Query
from pydantic import BaseModel,Field

from src.services.model_service import onnx_service

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent  # Points to project root
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions & content types
ALLOWED_EXTENSIONS = {".jpg", ".jpeg"}
ALLOWED_MIME_TYPES = {"image/jpeg"}

logger = logging.getLogger(__name__)

class PredictRequest(BaseModel):
    # Expecting 128 numerical values
    features: list[float] = Field(
        ..., min_length=128, max_length=128, example=[0.1] * 128
    )

@router.post("/predict")
async def predict_animal(request: PredictRequest):
    try:
        result = onnx_service.predict(request.features)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Inference error: {str(e)}"
        )

@router.post("/classify")
async def predict_animal_with_file(
        file: UploadFile = File(...),
        top_k: int = Query(5, ge=1)
):
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(
                status_code=400, detail="Uploaded file is empty."
            )

        predictions = onnx_service.classify_image(contents, top_k=top_k)
        return {"predictions": predictions}

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Inference error: {str(e)}"
        )

@router.post("/upload-image", status_code=status.HTTP_201_CREATED)
async def upload_animal_image(file: UploadFile = File(...)):
    # 1. Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension '{file_ext}'. Only .jpg and .jpeg are allowed.",
        )

    # 2. Validate MIME content-type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. File must be a JPEG image.",
        )

    # 3. Create destination path
    # (Optional: use UUID or timestamp to prevent overwriting existing files)
    save_path = UPLOAD_DIR / file.filename

    # 4. Save file to disk
    try:
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save image: {str(e)}",
        )
    finally:
        await file.close()

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "saved_location": str(save_path),
        "message": "File successfully uploaded",
    }