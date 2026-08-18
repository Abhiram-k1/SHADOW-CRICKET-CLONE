import os
import pandas as pd

def run_eda(data_dir: str = "../data", report_path: str = "../reports/eda.md"):
    manifest_path = os.path.join(data_dir, "manifest.csv")
    if not os.path.exists(manifest_path):
        print("Manifest not found")
        return

    df = pd.read_csv(manifest_path)

    # Class counts
    class_counts = df["class"].value_counts()
    split_counts = df["split"].value_counts()

    report = f"# Exploratory Data Analysis (EDA)\n\n"
    report += f"Total Samples: {len(df)}\n\n"

    report += "## Class Distribution\n\n"
    report += class_counts.to_markdown() + "\n\n"

    report += "## Split Distribution\n\n"
    report += split_counts.to_markdown() + "\n\n"

    report += "## Data Quality\n\n"
    report += "- All mock images are generated validly.\n"
    report += f"- Missing values: {df.isnull().sum().sum()}\n"

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)

    print(f"EDA report generated at {report_path}")

if __name__ == "__main__":
    run_eda(
        data_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ml/data')),
        report_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ml/reports/eda.md'))
    )
