import os
import pandas as pd
from PIL import Image
import numpy as np
import io

class Preprocessor:
    def __init__(self, target_size=(224, 224)):
        self.target_size = target_size

    def clean_image(self, image_bytes: bytes) -> bytes:
        """
        Reads image, checks for corruption, resizes and normalizes,
        returns deterministic compressed bytes.
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()

            # Reopen for processing after verify
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode != 'RGB':
                img = img.convert('RGB')

            img = img.resize(self.target_size, Image.Resampling.LANCZOS)

            # Standardize by saving out cleanly
            out_bytes = io.BytesIO()
            img.save(out_bytes, format="JPEG", quality=95)
            out_bytes.seek(0)
            return out_bytes.read()

        except Exception as e:
            raise ValueError(f"Corrupt or unreadable image: {e}")

def preprocess_dataset(data_dir: str = "../data"):
    manifest_path = os.path.join(data_dir, "manifest.csv")
    if not os.path.exists(manifest_path):
        return

    df = pd.read_csv(manifest_path)
    preprocessor = Preprocessor()

    cleaned_dir = os.path.join(data_dir, "images_cleaned")
    os.makedirs(cleaned_dir, exist_ok=True)

    success_count = 0

    for idx, row in df.iterrows():
        img_path = os.path.join(data_dir, row["image_path"])
        if not os.path.exists(img_path):
            continue

        with open(img_path, "rb") as f:
            raw_bytes = f.read()

        try:
            clean_bytes = preprocessor.clean_image(raw_bytes)
            # Replace original for training consistency in our mock setup,
            # or save to a clean dir. We'll just overwrite in place for simplicity.
            with open(img_path, "wb") as f:
                 f.write(clean_bytes)
            success_count += 1
        except Exception as e:
            print(f"Failed to preprocess {img_path}: {e}")

    print(f"Preprocessed {success_count} / {len(df)} images.")

if __name__ == "__main__":
    preprocess_dataset(data_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ml/data')))
