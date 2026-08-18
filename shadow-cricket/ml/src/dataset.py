import os
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from src.label_map import get_label_map

class CricketDataset(Dataset):
    def __init__(self, manifest_path: str, split: str = "train", data_dir: str = "../data", transform=None, use_cleaned=True):
        self.data_dir = data_dir
        self.transform = transform

        df = pd.read_csv(manifest_path)
        self.df = df[df["split"] == split].reset_index(drop=True)
        self.label_map = get_label_map()
        self.use_cleaned = use_cleaned

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        if self.use_cleaned:
            # We assume preprocess overwrote original for mock dataset
            img_path = os.path.join(self.data_dir, row["image_path"])
        else:
            img_path = os.path.join(self.data_dir, row["image_path"])

        img = Image.open(img_path).convert('RGB')

        if self.transform:
            img = self.transform(img)

        label = self.label_map[row["class"]]
        return img, torch.tensor(label, dtype=torch.long)

def get_dataloaders(manifest_path: str, data_dir: str, batch_size: int = 32, transform=None):
    train_ds = CricketDataset(manifest_path, split="train", data_dir=data_dir, transform=transform)
    val_ds = CricketDataset(manifest_path, split="val", data_dir=data_dir, transform=transform)
    test_ds = CricketDataset(manifest_path, split="test", data_dir=data_dir, transform=transform)

    train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_dl = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    test_dl = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    return train_dl, val_dl, test_dl
