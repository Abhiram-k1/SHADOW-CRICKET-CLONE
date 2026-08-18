# Model Evaluation Report (V1)

## Overall Metrics

| Model                        |   Accuracy |   Macro F1 |
|:-----------------------------|-----------:|-----------:|
| Baseline (ResNet18)          |   0.384615 |   0.27619  |
| Production (EfficientNet-B0) |   0.230769 |   0.214815 |

## Per-Class Metrics (EfficientNet)

| Class           |   Precision |   Recall |       F1 |
|:----------------|------------:|---------:|---------:|
| cover_drive     |        0    | 0        | 0        |
| forward_defense |        0.5  | 0.4      | 0.444444 |
| pull_shot       |        0.25 | 0.166667 | 0.2      |

## Confusion Matrix (EfficientNet)

|                 |   cover_drive |   forward_defense |   pull_shot |
|:----------------|--------------:|------------------:|------------:|
| cover_drive     |             0 |                 0 |           2 |
| forward_defense |             2 |                 2 |           1 |
| pull_shot       |             3 |                 2 |           1 |
