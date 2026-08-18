import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import io
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class InferenceResult:
    prediction: str
    confidence: float
    model_version: str
    scores: Dict[str, float]

class InferenceEngine:
    def __init__(self, model_version: str = "v1.0.0", checkpoint_path: str = None, label_map_path: str = None):
        self.model_version = model_version

        # Paths
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        if not checkpoint_path:
            checkpoint_path = os.path.join(base_dir, "checkpoints", "efficientnet_v1.pt")
        if not label_map_path:
            label_map_path = os.path.join(base_dir, "src", "label_map.json")

        # Load Label Map
        with open(label_map_path, "r") as f:
            self.label_map = json.load(f)

        self.idx_to_class = {v: k for k, v in self.label_map.items()}
        self.num_classes = len(self.label_map)

        # Load Model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = models.efficientnet_b0(pretrained=False)
        self.model.classifier[1] = nn.Linear(self.model.classifier[1].in_features, self.num_classes)
        self.model.load_state_dict(torch.load(checkpoint_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()

        # Transforms
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def predict(self, image_bytes: bytes) -> InferenceResult:
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        input_tensor = self.transform(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(input_tensor)
            probs = torch.nn.functional.softmax(outputs, dim=1)
            conf, predicted = torch.max(probs, 1)

        predicted_idx = predicted.item()
        confidence = conf.item()
        predicted_class = self.idx_to_class[predicted_idx]

        # Scores are computed outside in the main backend pipeline using mediapipe,
        # but we can return placeholders here if needed or let the caller attach them.

        return InferenceResult(
            prediction=predicted_class,
            confidence=confidence,
            model_version=self.model_version,
            scores={} # To be filled by deterministic scoring in Sprint 7
        )

# Global singleton for loaded engine
_engine = None

def get_engine() -> InferenceEngine:
    global _engine
    if _engine is None:
        _engine = InferenceEngine()
    return _engine

def run_inference(image_bytes: bytes) -> InferenceResult:
    engine = get_engine()
    return engine.predict(image_bytes)
