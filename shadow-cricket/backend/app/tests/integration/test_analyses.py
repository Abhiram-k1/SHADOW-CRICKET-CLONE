import io
import os
import sys

# Insert paths to allow importing from ml
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from fastapi.testclient import TestClient
from app.main import app
from PIL import Image

client = TestClient(app)

def create_test_image(size=(100, 100), format="JPEG"):
    file_obj = io.BytesIO()
    image = Image.new("RGB", size=size, color=(255, 0, 0))
    image.save(file_obj, format)
    file_obj.seek(0)
    return file_obj

def test_upload_valid_image():
    # Since we don't have header passing mock for auth right now, the deps fallback to the test user seeded via seed.py.
    # Therefore, ensure you run seed.py before tests, or use a mock db dependency in tests.
    file_obj = create_test_image()
    response = client.post(
        "/api/v1/analyses/",
        files={"file": ("test.jpg", file_obj, "image/jpeg")}
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    # The pure red image will likely result in a 'failed' status because mediapipe won't find a human
    assert data["status"] in ["completed", "failed"]
    assert "image_uri" in data
    return data["id"]

def test_get_analysis():
    analysis_id = test_upload_valid_image()
    response = client.get(f"/api/v1/analyses/{analysis_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == analysis_id
    assert data["status"] in ["completed", "failed"]

def test_upload_invalid_mime():
    response = client.post(
        "/api/v1/analyses/",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "UNSUPPORTED_MEDIA_TYPE"

def test_upload_corrupt_image():
    response = client.post(
        "/api/v1/analyses/",
        files={"file": ("test.jpg", io.BytesIO(b"not an image"), "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "INVALID_IMAGE"

if __name__ == "__main__":
    test_upload_valid_image()
