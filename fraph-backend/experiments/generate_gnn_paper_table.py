from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


PRIMARY_RUNS = {
    "fraud_data_kaggle_sample.csv": "20260330121604-fraud_data_kaggle_sample",
    "tmp/fraph_benchmark_slice.csv": "20260330163424-fraph_benchmark_slice",
    "tmp/fraph_benchmark_tiny.csv": "20260330163953-fraph_benchmark_tiny",
}
GNN_MODEL_NAMES = {"gnn", "gnn_graphsage", "gnn_gat"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a compact paper-ready GNN versus best baseline table.",
    )
    parser.add_argument(
        "--outputs-dir",
        default="outputs",
        help="Directory containing benchmark output runs.",
    )
    parser.add_argument(
        "--output",
        default="../../docs/paper/final_comparison_table.md",
        help="Path for the generated markdown table.",
    )
    return parser.parse_args()


def model_label(name: str) -> str:
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
    return aliases.get(name, name.replace("_", " ").title())


def metric(mean: str, std: str) -> str:
    return f"{float(mean):.4f} +- {float(std):.4f}"


def load_run(run_dir: Path) -> dict[str, object]:
    run_config = json.loads((run_dir / "run_config.json").read_text(encoding="utf-8"))
    with (run_dir / "summary_metrics.csv").open(newline="", encoding="utf-8") as handle:
        rows = {row["model_name"]: row for row in csv.DictReader(handle)}
    return {"config": run_config, "rows": rows}


def choose_best_row(rows: dict[str, dict[str, str]], allowed_names: set[str] | None = None, excluded_names: set[str] | None = None) -> tuple[str, dict[str, str]]:
    excluded = excluded_names or set()
    candidate_items = [
        (name, row)
        for name, row in rows.items()
        if (allowed_names is None or name in allowed_names) and name not in excluded
    ]
    if not candidate_items:
        raise ValueError("Run does not contain a compatible model for the requested selection.")
    best_name, best_row = max(
        candidate_items,
        key=lambda item: (
            float(item[1]["f1_mean"]),
            float(item[1]["pr_auc_mean"]),
            float(item[1]["roc_auc_mean"]),
        ),
    )
    return best_name, best_row


def choose_best_baseline(rows: dict[str, dict[str, str]]) -> tuple[str, dict[str, str]]:
    baseline_items = [
        (name, row) for name, row in rows.items()
        if name not in GNN_MODEL_NAMES
    ]
    if not baseline_items:
        raise ValueError("Run does not contain a baseline model.")
    best_name, best_row = max(
        baseline_items,
        key=lambda item: (
            float(item[1]["f1_mean"]),
            float(item[1]["pr_auc_mean"]),
            float(item[1]["roc_auc_mean"]),
        ),
    )
    return best_name, best_row


def build_records(outputs_dir: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for dataset_name, run_name in PRIMARY_RUNS.items():
        run_dir = outputs_dir / run_name
        if not run_dir.exists():
            continue

        payload = load_run(run_dir)
        rows = payload["rows"]
        if not any(name in GNN_MODEL_NAMES for name in rows):
            continue

        best_baseline_name, best_baseline_row = choose_best_baseline(rows)
        best_gnn_name, best_gnn_row = choose_best_row(rows, allowed_names=GNN_MODEL_NAMES)
        config = payload["config"]

        records.append(
            {
                "Dataset": dataset_name,
                "Run": run_name,
                "Protocol": f'{config["folds"]}-fold, seed {config["seed"]}',
                "Best Baseline": model_label(best_baseline_name),
                "Best GNN": model_label(best_gnn_name),
                "Baseline F1": metric(best_baseline_row["f1_mean"], best_baseline_row["f1_std"]),
                "GNN F1": metric(best_gnn_row["f1_mean"], best_gnn_row["f1_std"]),
                "Baseline PR-AUC": metric(best_baseline_row["pr_auc_mean"], best_baseline_row["pr_auc_std"]),
                "GNN PR-AUC": metric(best_gnn_row["pr_auc_mean"], best_gnn_row["pr_auc_std"]),
                "Baseline Recall": metric(best_baseline_row["recall_mean"], best_baseline_row["recall_std"]),
                "GNN Recall": metric(best_gnn_row["recall_mean"], best_gnn_row["recall_std"]),
                "GNN Threshold": metric(best_gnn_row["threshold_mean"], best_gnn_row["threshold_std"])
                if "threshold_mean" in best_gnn_row and "threshold_std" in best_gnn_row
                else "n/a",
            }
        )
    return records


def to_markdown(records: list[dict[str, str]]) -> str:
    lines = [
        "# Final Comparison Table",
        "",
        "One representative comparison is kept per dataset. For each selected run, the strongest non-GNN baseline and the strongest GNN-family model are shown. For `fraud_data_kaggle_sample.csv`, the selected source is the documented unified benchmark used in the draft paper. For the `tmp` benchmark datasets, the only available comparable run is used.",
        "",
        "| Dataset | Run | Protocol | Best Baseline | Best GNN | Baseline F1 | GNN F1 | Baseline PR-AUC | GNN PR-AUC | Baseline Recall | GNN Recall | GNN Threshold |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        lines.append(
            "| {Dataset} | {Run} | {Protocol} | {Best Baseline} | {Best GNN} | {Baseline F1} | {GNN F1} | {Baseline PR-AUC} | {GNN PR-AUC} | {Baseline Recall} | {GNN Recall} | {GNN Threshold} |".format(
                **record,
            )
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    outputs_dir = (script_dir.parent / args.outputs_dir).resolve()
    output_path = (script_dir / args.output).resolve()

    records = build_records(outputs_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(to_markdown(records), encoding="utf-8")
    print(f"Saved paper table to {output_path}")


if __name__ == "__main__":
    main()
