from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a markdown table comparing GNN against other models across saved benchmark runs.",
    )
    parser.add_argument(
        "--outputs-dir",
        default="outputs",
        help="Directory containing benchmark output runs.",
    )
    parser.add_argument(
        "--output",
        default="../../docs/paper/gnn_vs_models_all_datasets.md",
        help="Path for the generated markdown report.",
    )
    return parser.parse_args()


def format_metric(mean: str, std: str) -> str:
    return f"{float(mean):.4f} +- {float(std):.4f}"


def prettify_dataset(dataset_path: str) -> str:
    path = Path(dataset_path)
    parent_name = path.parent.name
    if parent_name == "datasets":
        return path.name
    if parent_name == "tmp":
        return f"tmp/{path.name}"
    return f"{parent_name}/{path.name}"


def prettify_model(model_name: str) -> str:
    aliases = {
        "gnn": "GNN",
        "knn": "KNN",
        "linear_svc": "Linear SVC",
        "logistic_regression": "Logistic Regression",
        "random_forest": "Random Forest",
        "gaussian_nb": "Gaussian NB",
        "gnn_graphsage": "GNN GraphSAGE",
        "gnn_gat": "GNN GAT",
    }
    return aliases.get(model_name, model_name.replace("_", " ").title())


def iter_comparison_runs(outputs_dir: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for run_dir in sorted(outputs_dir.iterdir()):
        if not run_dir.is_dir():
            continue

        run_config_path = run_dir / "run_config.json"
        summary_path = run_dir / "summary_metrics.csv"
        if not run_config_path.exists() or not summary_path.exists():
            continue

        run_config = json.loads(run_config_path.read_text(encoding="utf-8"))
        models = run_config.get("models", [])
        if "gnn" not in models or len(models) < 2:
            continue

        with summary_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        if not any(row["model_name"] == "gnn" for row in rows):
            continue

        dataset_label = prettify_dataset(run_config["dataset"])
        for row in sorted(rows, key=lambda item: (item["model_name"] != "gnn", item["model_name"])):
            records.append(
                {
                    "dataset": dataset_label,
                    "run_name": run_dir.name,
                    "models_in_run": ", ".join(prettify_model(model) for model in models),
                    "model": prettify_model(row["model_name"]),
                    "accuracy": format_metric(row["accuracy_mean"], row["accuracy_std"]),
                    "precision": format_metric(row["precision_mean"], row["precision_std"]),
                    "recall": format_metric(row["recall_mean"], row["recall_std"]),
                    "f1": format_metric(row["f1_mean"], row["f1_std"]),
                    "roc_auc": format_metric(row["roc_auc_mean"], row["roc_auc_std"]),
                    "pr_auc": format_metric(row["pr_auc_mean"], row["pr_auc_std"]),
                    "mcc": format_metric(row["mcc_mean"], row["mcc_std"]),
                }
            )
    return records


def build_markdown(records: list[dict[str, object]]) -> str:
    lines = [
        "# GNN vs Other Models Across Saved Benchmarks",
        "",
        "This report scans saved benchmark outputs and keeps only runs where `GNN` was evaluated together with at least one non-GNN model.",
        "",
        "| Dataset | Run | Models In Run | Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC | MCC |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for record in records:
        lines.append(
            "| {dataset} | {run_name} | {models_in_run} | {model} | {accuracy} | {precision} | {recall} | {f1} | {roc_auc} | {pr_auc} | {mcc} |".format(
                **record,
            )
        )

    if not records:
        lines.append("| No comparable runs found | - | - | - | - | - | - | - | - | - | - |")

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    outputs_dir = (script_dir.parent / args.outputs_dir).resolve()
    output_path = (script_dir / args.output).resolve()

    records = iter_comparison_runs(outputs_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown(records), encoding="utf-8")
    print(f"Saved report to {output_path}")


if __name__ == "__main__":
    main()
