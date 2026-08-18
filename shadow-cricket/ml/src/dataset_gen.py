import os
import pandas as pd
import numpy as np
import uuid
from PIL import Image

def generate_mock_dataset(data_dir: str = "../data", num_samples: int = 50):
    os.makedirs(data_dir, exist_ok=True)
    images_dir = os.path.join(data_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    classes = ["forward_defense", "cover_drive", "pull_shot"]
    splits = ["train", "val", "test"]
    split_probs = [0.7, 0.15, 0.15]

    manifest_data = []

    for i in range(num_samples):
        class_label = np.random.choice(classes)
        split = np.random.choice(splits, p=split_probs)
        img_id = str(uuid.uuid4())
        filename = f"{img_id}.jpg"
        filepath = os.path.join(images_dir, filename)

        # Create a mock image with random solid color representing a posture
        color = tuple(np.random.randint(0, 255, 3))
        img = Image.new("RGB", (224, 224), color=color)
        img.save(filepath, "JPEG")

        manifest_data.append({
            "image_path": f"images/{filename}",
            "source_dataset": "mock_dataset",
            "class": class_label,
            "split": split,
            "quality_flag": "good",
            "subject_id": f"sub_{np.random.randint(1, 5)}"
        })

    df = pd.DataFrame(manifest_data)
    df.to_csv(os.path.join(data_dir, "manifest.csv"), index=False)
    print(f"Generated mock dataset with {num_samples} images at {data_dir}/manifest.csv")

if __name__ == "__main__":
    generate_mock_dataset(data_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
