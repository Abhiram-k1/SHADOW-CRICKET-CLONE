import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml.src.infer import run_inference
from PIL import Image
import io

def test_inference():
    file_obj = io.BytesIO()
    image = Image.new("RGB", size=(400, 400), color=(255, 0, 0))
    image.save(file_obj, "JPEG")
    file_obj.seek(0)

    result = run_inference(file_obj.read())
    print("Inference successful:")
    print("Prediction:", result.prediction)
    print("Confidence:", result.confidence)

if __name__ == "__main__":
    test_inference()
