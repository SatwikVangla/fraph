import json
from pathlib import Path

import matplotlib.pyplot as plt

from app.utils.helpers import build_model_storage_path


def generate_model_report(
    dataset_name: str,
    model_name: str,
    result: dict[str, object],
) -> dict[str, str | None]:
    metrics_to_plot = [
        ("Accuracy", result.get("accuracy")),
        ("Precision", result.get("precision")),
        ("Recall", result.get("recall")),
        ("F1", result.get("f1_score")),
        ("ROC-AUC", result.get("roc_auc")),
        ("PR-AUC", result.get("pr_auc")),
        ("MCC", result.get("mcc")),
    ]
    chart_path = build_model_storage_path(dataset_name, f"{model_name}-metrics", ".png")
    report_path = build_model_storage_path(dataset_name, f"{model_name}-report", ".md")
    json_path = build_model_storage_path(dataset_name, f"{model_name}-report", ".json")

    labels = [label for label, value in metrics_to_plot if value is not None]
    values = [float(value) for _label, value in metrics_to_plot if value is not None]
    if labels and values:
        figure, axis = plt.subplots(figsize=(8, 4.5))
        axis.bar(labels, values, color="#cf1825")
        axis.set_ylim(0, 1)
        axis.set_title(f"{model_name} metrics")
        axis.tick_params(axis="x", rotation=25)
        axis.grid(axis="y", alpha=0.2)
        figure.tight_layout()
        figure.savefig(chart_path, dpi=180)
        plt.close(figure)
        chart_ref = str(chart_path)
    else:
        chart_ref = None

    markdown = "\n".join(
        [
            f"# {model_name} report",
            "",
            f"- Dataset: `{dataset_name}`",
            f"- Model: `{model_name}`",
            f"- Status: `{result.get('status')}`",
            f"- Artifact path: `{result.get('artifact_path')}`",
            f"- Metrics chart: `{chart_ref}`",
            "",
            "## Metrics",
            "",
            *(f"- {label}: `{value}`" for label, value in metrics_to_plot),
            "",
            "## Details",
            "",
            f"{result.get('details', '')}",
            "",
            "## Diagnostics",
            "",
            f"```json\n{json.dumps(result.get('diagnostics', {}), indent=2)}\n```",
            "",
            "## Explainability",
            "",
            f"```json\n{json.dumps(result.get('explainability', {}), indent=2)}\n```",
            "",
            "## Selected Config",
            "",
            f"```json\n{json.dumps(result.get('selected_config', {}), indent=2)}\n```",
            "",
        ]
    )
    report_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    return {
        "report_path": str(report_path),
        "report_json_path": str(json_path),
        "report_chart_path": chart_ref,
    }
