import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models, transforms
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.dataset import get_dataloaders
from src.label_map import get_label_map

def train_baseline(data_dir: str = "../data", epochs: int = 2):
    manifest_path = os.path.join(data_dir, "manifest.csv")
    label_map = get_label_map()
    num_classes = len(label_map)

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_dl, val_dl, _ = get_dataloaders(manifest_path, data_dir, batch_size=16, transform=transform)

    model = models.resnet18(pretrained=True)
    model.fc = nn.Linear(model.fc.in_features, num_classes)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    print("Training baseline model (ResNet18 mock)")
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for inputs, labels in train_dl:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

        print(f"Epoch {epoch+1}/{epochs}, Loss: {running_loss/len(train_dl):.4f}")

    os.makedirs("../checkpoints", exist_ok=True)
    torch.save(model.state_dict(), "../checkpoints/baseline.pt")
    print("Baseline model saved.")

def train_efficientnet(data_dir: str = "../data", epochs: int = 2):
    manifest_path = os.path.join(data_dir, "manifest.csv")
    label_map = get_label_map()
    num_classes = len(label_map)

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_dl, val_dl, _ = get_dataloaders(manifest_path, data_dir, batch_size=16, transform=transform)

    # We use a smaller EfficientNet config (b0) for speed in mock training
    model = models.efficientnet_b0(pretrained=True)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=3e-4)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    print("Training production model (EfficientNet-B0)")
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for inputs, labels in train_dl:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

        print(f"Epoch {epoch+1}/{epochs}, Loss: {running_loss/len(train_dl):.4f}")

    os.makedirs("../checkpoints", exist_ok=True)
    torch.save(model.state_dict(), "../checkpoints/efficientnet_v1.pt")
    print("EfficientNet model saved.")

if __name__ == "__main__":
    train_baseline(data_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ml/data')), epochs=1)
    train_efficientnet(data_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ml/data')), epochs=1)
