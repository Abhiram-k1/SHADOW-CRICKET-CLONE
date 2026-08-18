import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support, confusion_matrix
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.dataset import get_dataloaders
from src.label_map import get_label_map
from tabulate import tabulate

def evaluate_models(data_dir: str = "../data", report_path: str = "../../ml/reports/eval_v1.md"):
    manifest_path = os.path.join(data_dir, "manifest.csv")
    label_map = get_label_map()
    num_classes = len(label_map)
    idx_to_class = {v: k for k, v in label_map.items()}
    class_names = [idx_to_class[i] for i in range(num_classes)]

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    _, _, test_dl = get_dataloaders(manifest_path, data_dir, batch_size=16, transform=transform)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 1. Baseline Model
    baseline = models.resnet18(pretrained=False)
    baseline.fc = nn.Linear(baseline.fc.in_features, num_classes)
    baseline.load_state_dict(torch.load("../checkpoints/baseline.pt", map_location=device))
    baseline.to(device)
    baseline.eval()

    # 2. EfficientNet Model
    effnet = models.efficientnet_b0(pretrained=False)
    effnet.classifier[1] = nn.Linear(effnet.classifier[1].in_features, num_classes)
    effnet.load_state_dict(torch.load("../checkpoints/efficientnet_v1.pt", map_location=device))
    effnet.to(device)
    effnet.eval()

    def get_preds(model, dataloader):
        all_preds = []
        all_labels = []
        with torch.no_grad():
            for inputs, labels in dataloader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        return np.array(all_labels), np.array(all_preds)

    y_true, y_pred_base = get_preds(baseline, test_dl)
    y_true, y_pred_eff = get_preds(effnet, test_dl)

    def get_metrics(y_true, y_pred):
        acc = accuracy_score(y_true, y_pred)
        mac_f1 = f1_score(y_true, y_pred, average="macro")
        p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, labels=list(range(num_classes)))
        cm = confusion_matrix(y_true, y_pred, labels=list(range(num_classes)))
        return acc, mac_f1, p, r, f1, cm

    base_acc, base_f1, base_p, base_r, base_f1s, base_cm = get_metrics(y_true, y_pred_base)
    eff_acc, eff_f1, eff_p, eff_r, eff_f1s, eff_cm = get_metrics(y_true, y_pred_eff)

    report = f"# Model Evaluation Report (V1)\n\n"
    report += "## Overall Metrics\n\n"
    metrics_df = pd.DataFrame({
        "Model": ["Baseline (ResNet18)", "Production (EfficientNet-B0)"],
        "Accuracy": [base_acc, eff_acc],
        "Macro F1": [base_f1, eff_f1]
    })
    report += tabulate(metrics_df, headers='keys', tablefmt='pipe', showindex=False) + "\n\n"

    report += "## Per-Class Metrics (EfficientNet)\n\n"
    class_df = pd.DataFrame({
        "Class": class_names,
        "Precision": eff_p,
        "Recall": eff_r,
        "F1": eff_f1s
    })
    report += tabulate(class_df, headers='keys', tablefmt='pipe', showindex=False) + "\n\n"

    report += "## Confusion Matrix (EfficientNet)\n\n"
    cm_df = pd.DataFrame(eff_cm, index=class_names, columns=class_names)
    report += tabulate(cm_df, headers='keys', tablefmt='pipe') + "\n\n"

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)

    print(f"Evaluation report generated at {report_path}")

if __name__ == "__main__":
    evaluate_models(
        data_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ml/data')),
        report_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ml/reports/eval_v1.md'))
    )
