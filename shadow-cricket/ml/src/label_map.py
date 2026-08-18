import os
import pandas as pd
import json

LABEL_MAP_FILE = os.path.join(os.path.dirname(__file__), "label_map.json")

def generate_label_map(manifest_path: str = "../data/manifest.csv") -> dict:
    df = pd.read_csv(manifest_path)
    classes = sorted(df["class"].unique().tolist())
    label_map = {cls: idx for idx, cls in enumerate(classes)}

    with open(LABEL_MAP_FILE, "w") as f:
        json.dump(label_map, f, indent=4)

    return label_map

def get_label_map() -> dict:
    if not os.path.exists(LABEL_MAP_FILE):
        return generate_label_map(os.path.join(os.path.dirname(__file__), '../../ml/data/manifest.csv'))

    with open(LABEL_MAP_FILE, "r") as f:
        return json.load(f)

def validate_manifest(manifest_path: str = "../data/manifest.csv"):
    label_map = get_label_map()
    df = pd.read_csv(manifest_path)
    manifest_classes = set(df["class"].unique())
    label_map_classes = set(label_map.keys())

    missing_in_map = manifest_classes - label_map_classes
    if missing_in_map:
        raise ValueError(f"Classes in manifest missing from label map: {missing_in_map}")

if __name__ == "__main__":
    generate_label_map(os.path.join(os.path.dirname(__file__), '../../ml/data/manifest.csv'))
    validate_manifest(os.path.join(os.path.dirname(__file__), '../../ml/data/manifest.csv'))
    print("Label map consistency verified.")
