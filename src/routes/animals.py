import logging
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile, status, Query

from src.services.model_service import onnx_service

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent  # Points to project root
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions & content types
ALLOWED_EXTENSIONS = {".jpg", ".jpeg"}
ALLOWED_MIME_TYPES = {"image/jpeg"}

logger = logging.getLogger(__name__)

@router.post("/classifyDogAndCats")
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
