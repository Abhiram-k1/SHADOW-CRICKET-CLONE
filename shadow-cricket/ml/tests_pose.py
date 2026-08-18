import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml.src.pose import pose_extractor
from PIL import Image
import io

def test_extract_landmarks():
    file_obj = io.BytesIO()
    # create dummy image. Need to have a somewhat realistic posture to be detected easily, or skip assertions if not found
    image = Image.new("RGB", size=(400, 400), color=(255, 255, 255))
    image.save(file_obj, "JPEG")
    file_obj.seek(0)

    # Try to extract (might be None for blank image, which is fine for smoke test)
    landmarks = pose_extractor.extract_landmarks(file_obj.read())
    print("Test passed (completed gracefully). Landmarks extracted:", bool(landmarks))

if __name__ == "__main__":
    test_extract_landmarks()
