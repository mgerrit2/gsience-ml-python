import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status, Query
from pydantic import BaseModel

from src.schemes.PredictionResult import PredictionResult
from src.services.model_service import onnx_service

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent  # Points to project root
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions & content types
ALLOWED_EXTENSIONS = {".jpg", ".jpeg"}
ALLOWED_MIME_TYPES = {"image/jpeg"}

logger = logging.getLogger(__name__)

class PredictionResponse(BaseModel):
    predictions: list[PredictionResult]

@router.post(
    "/classifyDogAndCats",
    status_code=status.HTTP_200_OK,
    response_model=PredictionResponse,
    responses={
        200: {
            "description": "Successfully retrieved list",
            # Content schema is automatically generated via response_model=list[CompanyDTO]
        },
        400: {"description": "Bad Request, missing required fields."},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not Found"},
        406: {"description": "Not Acceptable"},
        415: {"description": "Bad Request, missing required fields."},
        429: {"description": "Retry After Some Time"},
        500: {"description": "Internal Server Error" },
    },
)
async def predict_animal_with_file(
        file: Annotated[UploadFile, File(...)],
        top_k: Annotated[int, Query(ge=1)] = 5
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
