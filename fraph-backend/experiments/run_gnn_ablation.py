from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from experiments.run_benchmark import run_benchmark


ABLATIONS = [
    {
        "name": "full_gnn",
        "gnn_use_similarity_edges": True,
        "gnn_use_party_edges": True,
        "gnn_use_class_weights": True,
    },
    {
        "name": "no_similarity_edges",
        "gnn_use_similarity_edges": False,
        "gnn_use_party_edges": True,
        "gnn_use_class_weights": True,
    },
    {
        "name": "no_party_edges",
        "gnn_use_similarity_edges": True,
        "gnn_use_party_edges": False,
        "gnn_use_class_weights": True,
    },
    {
        "name": "no_class_weights",
        "gnn_use_similarity_edges": True,
        "gnn_use_party_edges": True,
        "gnn_use_class_weights": False,
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run GNN ablation experiments.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--gnn-epochs", type=int, default=20)
    parser.add_argument("--gnn-hidden-dim", type=int, default=32)
    parser.add_argument("--gnn-learning-rate", type=float, default=0.01)
    parser.add_argument("--gnn-dropout", type=float, default=0.2)
    parser.add_argument("--output-dir", default="outputs")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ablation_rows: list[dict[str, object]] = []
    dataset_stem = Path(args.dataset).stem

    for ablation in ABLATIONS:
        result = run_benchmark(
            dataset=args.dataset,
            models=["gnn"],
            folds=args.folds,
            repeats=args.repeats,
            seed=args.seed,
            gnn_epochs=args.gnn_epochs,
            gnn_hidden_dim=args.gnn_hidden_dim,
            gnn_learning_rate=args.gnn_learning_rate,
            gnn_dropout=args.gnn_dropout,
            output_dir=args.output_dir,
            output_suffix=f"ablation-{ablation['name']}",
            gnn_use_similarity_edges=ablation["gnn_use_similarity_edges"],
            gnn_use_party_edges=ablation["gnn_use_party_edges"],
            gnn_use_class_weights=ablation["gnn_use_class_weights"],
        )
        summary = result["summary"].iloc[0].to_dict()
        ablation_rows.append(
            {
                "dataset": dataset_stem,
                "ablation": ablation["name"],
                **summary,
                "output_root": result["output_root"],
            }
        )

    ablation_frame = pd.DataFrame(ablation_rows).sort_values(
        by=["f1_mean", "pr_auc_mean", "roc_auc_mean"],
        ascending=False,
    )
    output_root = Path(args.output_dir) / f"{dataset_stem}-gnn-ablation"
    output_root.mkdir(parents=True, exist_ok=True)
    ablation_frame.to_csv(output_root / "ablation_results.csv", index=False)
    ablation_frame.to_json(output_root / "ablation_results.json", orient="records", indent=2)
    print(f"Saved ablation results to {output_root}")


if __name__ == "__main__":
    main()
