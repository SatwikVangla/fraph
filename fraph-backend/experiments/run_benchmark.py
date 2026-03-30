from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/fraph-matplotlib")

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_recall_curve,
    roc_curve,
)
from sklearn.model_selection import RepeatedStratifiedKFold

from app.services.gnn_model import build_transaction_graph_from_prepared, train_gnn_from_graph
from app.services.ml_models import (
    evaluate_model,
    get_model_probabilities,
    get_model_specs,
    prepare_labeled_dataset,
)

DEFAULT_MODELS = [
    "knn",
    "logistic_regression",
    "linear_svc",
    "random_forest",
    "gnn",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run paper-style repeated stratified evaluation for FRAPH models.",
    )
    parser.add_argument("--dataset", required=True, help="Path to a labeled CSV dataset.")
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODELS,
        help="Models to evaluate.",
    )
    parser.add_argument("--folds", type=int, default=5, help="Number of CV folds.")
    parser.add_argument("--repeats", type=int, default=3, help="Number of repeated CV rounds.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--gnn-epochs", type=int, default=20)
    parser.add_argument("--gnn-hidden-dim", type=int, default=32)
    parser.add_argument("--gnn-learning-rate", type=float, default=0.01)
    parser.add_argument("--gnn-dropout", type=float, default=0.2)
    parser.add_argument("--gnn-use-similarity-edges", action="store_true", default=True)
    parser.add_argument("--gnn-disable-similarity-edges", action="store_false", dest="gnn_use_similarity_edges")
    parser.add_argument("--gnn-use-party-edges", action="store_true", default=True)
    parser.add_argument("--gnn-disable-party-edges", action="store_false", dest="gnn_use_party_edges")
    parser.add_argument("--gnn-use-class-weights", action="store_true", default=True)
    parser.add_argument("--gnn-disable-class-weights", action="store_false", dest="gnn_use_class_weights")
    parser.add_argument("--output-dir", default="outputs", help="Output directory.")
    return parser.parse_args()


def build_output_paths(output_dir: str, dataset_path: Path, suffix: str | None = None) -> tuple[Path, Path]:
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    run_name = f"{timestamp}-{dataset_path.stem}"
    if suffix:
        run_name = f"{run_name}-{suffix}"
    root = Path(output_dir) / run_name
    plots = root / "plots"
    plots.mkdir(parents=True, exist_ok=True)
    return root, plots


def evaluate_classical_model(
    model_name: str,
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_test: pd.DataFrame,
    y_test: pd.Series,
) -> tuple[dict[str, object], list[float], list[int], list[int]]:
    model = get_model_specs()[model_name]
    model.fit(x_train, y_train)
    metrics = evaluate_model(model_name, model, x_test, y_test)
    probabilities = list(get_model_probabilities(model, x_test))
    predictions = list(model.predict(x_test))
    return metrics, probabilities, predictions, list(y_test)


def evaluate_gnn_model(
    prepared: pd.DataFrame,
    train_indices: list[int],
    test_indices: list[int],
    dataset_name: str,
    epochs: int,
    hidden_dim: int,
    learning_rate: float,
    dropout: float,
    fold_name: str,
    use_similarity_edges: bool,
    use_party_edges: bool,
    use_class_weights: bool,
) -> tuple[dict[str, object], list[float], list[int], list[int]]:
    graph = build_transaction_graph_from_prepared(
        prepared=prepared,
        train_indices=train_indices,
        test_indices=test_indices,
        random_state=42,
        use_similarity_edges=use_similarity_edges,
        use_party_edges=use_party_edges,
    )
    result = train_gnn_from_graph(
        graph=graph,
        dataset_name=dataset_name,
        epochs=epochs,
        hidden_dim=hidden_dim,
        learning_rate=learning_rate,
        artifact_name=f"gnn-{fold_name}",
        persist_artifact=False,
        include_raw_outputs=True,
        use_class_weights=use_class_weights,
        dropout=dropout,
    )
    raw_outputs = result.pop("raw_outputs")
    return result, raw_outputs["probabilities"], raw_outputs["predictions"], raw_outputs["y_true"]


def save_summary_table(summary: pd.DataFrame, output_root: Path) -> None:
    summary.to_csv(output_root / "summary_metrics.csv", index=False)
    headers = summary.columns.tolist()
    separator = ["---"] * len(headers)
    rows = summary.astype(str).values.tolist()
    markdown_lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    markdown_lines.extend("| " + " | ".join(row) + " |" for row in rows)
    (output_root / "summary_metrics.md").write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")


def plot_curve(
    x_values,
    y_values,
    title: str,
    x_label: str,
    y_label: str,
    output_path: Path,
) -> None:
    plt.figure(figsize=(7, 5))
    plt.plot(x_values, y_values, linewidth=2)
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def plot_confusion_matrix(matrix, title: str, output_path: Path) -> None:
    fig, axis = plt.subplots(figsize=(5, 4))
    image = axis.imshow(matrix, cmap="Reds")
    axis.figure.colorbar(image, ax=axis)
    axis.set_title(title)
    axis.set_xlabel("Predicted")
    axis.set_ylabel("Actual")
    axis.set_xticks([0, 1], labels=["Legit", "Fraud"])
    axis.set_yticks([0, 1], labels=["Legit", "Fraud"])
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            axis.text(column, row, int(matrix[row, column]), ha="center", va="center")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def summarize_fold_metrics(fold_metrics: pd.DataFrame) -> pd.DataFrame:
    summary = (
        fold_metrics.groupby("model_name")
        .agg({
            "accuracy": ["mean", "std"],
            "precision": ["mean", "std"],
            "recall": ["mean", "std"],
            "f1_score": ["mean", "std"],
            "roc_auc": ["mean", "std"],
            "pr_auc": ["mean", "std"],
            "mcc": ["mean", "std"],
        })
        .reset_index()
    )
    summary.columns = [
        "model_name",
        "accuracy_mean",
        "accuracy_std",
        "precision_mean",
        "precision_std",
        "recall_mean",
        "recall_std",
        "f1_mean",
        "f1_std",
        "roc_auc_mean",
        "roc_auc_std",
        "pr_auc_mean",
        "pr_auc_std",
        "mcc_mean",
        "mcc_std",
    ]
    return summary


def run_benchmark(
    dataset: str,
    models: list[str] | None = None,
    folds: int = 5,
    repeats: int = 3,
    seed: int = 42,
    gnn_epochs: int = 20,
    gnn_hidden_dim: int = 32,
    gnn_learning_rate: float = 0.01,
    gnn_dropout: float = 0.2,
    gnn_use_similarity_edges: bool = True,
    gnn_use_party_edges: bool = True,
    gnn_use_class_weights: bool = True,
    output_dir: str = "outputs",
    output_suffix: str | None = None,
) -> dict[str, object]:
    dataset_path = Path(dataset).resolve()
    output_root, plots_dir = build_output_paths(output_dir, dataset_path, suffix=output_suffix)

    labeled, features, labels = prepare_labeled_dataset(str(dataset_path))
    prepared = labeled.reset_index(drop=True).copy()
    labels = labels.reset_index(drop=True)
    model_list = models or DEFAULT_MODELS

    splitter = RepeatedStratifiedKFold(
        n_splits=folds,
        n_repeats=repeats,
        random_state=seed,
    )

    fold_rows: list[dict[str, object]] = []
    plot_payloads = {
        model_name: {"y_true": [], "probabilities": [], "predictions": []}
        for model_name in model_list
    }

    for fold_index, (train_idx, test_idx) in enumerate(splitter.split(features, labels), start=1):
        x_train = features.iloc[train_idx]
        x_test = features.iloc[test_idx]
        y_train = labels.iloc[train_idx]
        y_test = labels.iloc[test_idx]
        fold_name = f"fold-{fold_index}"

        for model_name in model_list:
            if model_name == "gnn":
                result, probabilities, predictions, y_true = evaluate_gnn_model(
                    prepared=prepared,
                    train_indices=list(train_idx),
                    test_indices=list(test_idx),
                    dataset_name=dataset_path.stem,
                    epochs=gnn_epochs,
                    hidden_dim=gnn_hidden_dim,
                    learning_rate=gnn_learning_rate,
                    dropout=gnn_dropout,
                    fold_name=fold_name,
                    use_similarity_edges=gnn_use_similarity_edges,
                    use_party_edges=gnn_use_party_edges,
                    use_class_weights=gnn_use_class_weights,
                )
            else:
                result, probabilities, predictions, y_true = evaluate_classical_model(
                    model_name=model_name,
                    x_train=x_train,
                    y_train=y_train,
                    x_test=x_test,
                    y_test=y_test,
                )

            fold_rows.append(
                {
                    "fold": fold_index,
                    "model_name": model_name,
                    "accuracy": result["accuracy"],
                    "precision": result["precision"],
                    "recall": result["recall"],
                    "f1_score": result["f1_score"],
                    "roc_auc": result["roc_auc"],
                    "pr_auc": result.get("pr_auc"),
                    "mcc": result.get("mcc"),
                    "tn": result.get("tn"),
                    "fp": result.get("fp"),
                    "fn": result.get("fn"),
                    "tp": result.get("tp"),
                }
            )

            if probabilities and predictions and y_true:
                plot_payloads[model_name]["y_true"].extend(y_true)
                plot_payloads[model_name]["probabilities"].extend(probabilities)
                plot_payloads[model_name]["predictions"].extend(predictions)

    fold_metrics = pd.DataFrame(fold_rows)
    fold_metrics.to_csv(output_root / "fold_metrics.csv", index=False)
    fold_metrics.to_json(output_root / "fold_metrics.json", orient="records", indent=2)

    summary = summarize_fold_metrics(fold_metrics)
    save_summary_table(summary, output_root)

    for model_name, payload in plot_payloads.items():
        y_true = payload["y_true"]
        probabilities = payload["probabilities"]
        predictions = payload["predictions"]
        if not y_true or not probabilities or not predictions:
            continue
        precision, recall, _ = precision_recall_curve(y_true, probabilities)
        fpr, tpr, _ = roc_curve(y_true, probabilities)
        ap_score = average_precision_score(y_true, probabilities)
        confusion = confusion_matrix(y_true, predictions, labels=[0, 1])
        plot_curve(
            recall,
            precision,
            f"{model_name} Precision-Recall Curve (AP={ap_score:.4f})",
            "Recall",
            "Precision",
            plots_dir / f"{model_name}_pr_curve.png",
        )
        plot_curve(
            fpr,
            tpr,
            f"{model_name} ROC Curve",
            "False Positive Rate",
            "True Positive Rate",
            plots_dir / f"{model_name}_roc_curve.png",
        )
        plot_confusion_matrix(
            confusion,
            f"{model_name} Confusion Matrix",
            plots_dir / f"{model_name}_confusion_matrix.png",
        )

    config = {
        "dataset": str(dataset_path),
        "models": model_list,
        "folds": folds,
        "repeats": repeats,
        "seed": seed,
        "gnn_epochs": gnn_epochs,
        "gnn_hidden_dim": gnn_hidden_dim,
        "gnn_learning_rate": gnn_learning_rate,
        "gnn_dropout": gnn_dropout,
        "gnn_use_similarity_edges": gnn_use_similarity_edges,
        "gnn_use_party_edges": gnn_use_party_edges,
        "gnn_use_class_weights": gnn_use_class_weights,
    }
    (output_root / "run_config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return {
        "output_root": str(output_root),
        "summary": summary,
        "fold_metrics": fold_metrics,
    }


def main() -> None:
    args = parse_args()
    result = run_benchmark(
        dataset=args.dataset,
        models=args.models,
        folds=args.folds,
        repeats=args.repeats,
        seed=args.seed,
        gnn_epochs=args.gnn_epochs,
        gnn_hidden_dim=args.gnn_hidden_dim,
        gnn_learning_rate=args.gnn_learning_rate,
        gnn_dropout=args.gnn_dropout,
        gnn_use_similarity_edges=args.gnn_use_similarity_edges,
        gnn_use_party_edges=args.gnn_use_party_edges,
        gnn_use_class_weights=args.gnn_use_class_weights,
        output_dir=args.output_dir,
    )
    print(f"Saved experiment outputs to {result['output_root']}")


if __name__ == "__main__":
    main()
