from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.routes.animals import router

# Setup a test app and include your router
app = FastAPI()
app.include_router(router)

client = TestClient(app)


@patch("src.routes.animals.onnx_service.classify_image")
def test_predict_animal_success(mock_classify):
    # 1. Configure the mock to return objects/dicts matching the PredictionResult schema
    mock_classify.return_value = [
        {
            "class_id": 281,
            "label": "cat",
            "probability": "95.00%"
        },
        {
            "class_id": 282,
            "label": "dog",
            "probability": "5.00%"
        }
    ]

    # 2. Create a dummy image file payload for the multipart/form-data upload
    fake_image_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"  # fake JPEG header bytes
    files = {"file": ("test_cat.jpg", fake_image_bytes, "image/jpeg")}

    # 3. Call the endpoint
    response = client.post("/classifyDogAndCats?top_k=2", files=files)

    # 4. Assertions
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert len(data["predictions"]) == 2
    assert data["predictions"][0]["label"] == "cat"

    # Verify that the service was called with the file bytes and top_k
    mock_classify.assert_called_once_with(fake_image_bytes, top_k=2)


@patch("src.routes.animals.onnx_service.classify_image")
def test_predict_animal_value_error(mock_classify):
    # Test handling of a ValueError from the service (e.g., invalid image format)
    mock_classify.side_effect = ValueError("Invalid image dimensions")

    fake_image_bytes = b"bad_image_data"
    files = {"file": ("bad.jpg", fake_image_bytes, "image/jpeg")}

    response = client.post("/classifyDogAndCats", files=files)

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image dimensions"


@pytest.mark.skip(reason="Temporarily disabled")
@patch("src.routes.animals.onnx_service.classify_image")
def test_predict_animal_empty_file(mock_classify):
    # Test uploading an empty file (handled before service call)
    files = {"file": ("empty.jpg", b"", "image/jpeg")}

    response = client.post("/classifyDogAndCats", files=files)

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty."