from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path

import pandas as pd

from experiments.run_benchmark import run_benchmark


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Expected a boolean value, got: {value}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a GNN hyperparameter sweep.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", nargs="+", type=int, default=[10, 20, 30])
    parser.add_argument("--hidden-dims", nargs="+", type=int, default=[16, 32, 64])
    parser.add_argument("--learning-rates", nargs="+", type=float, default=[0.01, 0.005])
    parser.add_argument("--dropouts", nargs="+", type=float, default=[0.1, 0.2, 0.3])
    parser.add_argument(
        "--architectures",
        nargs="+",
        default=["gnn", "gnn_graphsage", "gnn_gat"],
        choices=["gnn", "gnn_graphsage", "gnn_gat"],
    )
    parser.add_argument("--similarity-edge-options", nargs="+", type=parse_bool, default=[True, False])
    parser.add_argument("--party-edge-options", nargs="+", type=parse_bool, default=[True, False])
    parser.add_argument("--temporal-edge-options", nargs="+", type=parse_bool, default=[True])
    parser.add_argument("--account-node-options", nargs="+", type=parse_bool, default=[True, False])
    parser.add_argument("--output-dir", default="outputs")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sweep_rows: list[dict[str, object]] = []
    dataset_stem = Path(args.dataset).stem

    for architecture, epochs, hidden_dim, learning_rate, dropout, use_similarity_edges, use_party_edges, use_temporal_edges, include_account_nodes in product(
        args.architectures,
        args.epochs,
        args.hidden_dims,
        args.learning_rates,
        args.dropouts,
        args.similarity_edge_options,
        args.party_edge_options,
        args.temporal_edge_options,
        args.account_node_options,
    ):
        suffix = (
            f"sweep-{architecture}"
            f"-e{epochs}-h{hidden_dim}-lr{learning_rate}-d{dropout}"
            f"-sim{int(use_similarity_edges)}-party{int(use_party_edges)}"
            f"-temp{int(use_temporal_edges)}-acct{int(include_account_nodes)}"
        )
        result = run_benchmark(
            dataset=args.dataset,
            models=[architecture],
            folds=args.folds,
            repeats=args.repeats,
            seed=args.seed,
            gnn_epochs=epochs,
            gnn_hidden_dim=hidden_dim,
            gnn_learning_rate=learning_rate,
            gnn_dropout=dropout,
            gnn_use_similarity_edges=use_similarity_edges,
            gnn_use_party_edges=use_party_edges,
            gnn_use_temporal_edges=use_temporal_edges,
            gnn_include_account_nodes=include_account_nodes,
            output_dir=args.output_dir,
            output_suffix=suffix,
        )
        summary = result["summary"].iloc[0].to_dict()
        sweep_rows.append(
            {
                "dataset": dataset_stem,
                "architecture": architecture,
                "epochs": epochs,
                "hidden_dim": hidden_dim,
                "learning_rate": learning_rate,
                "dropout": dropout,
                "use_similarity_edges": use_similarity_edges,
                "use_party_edges": use_party_edges,
                "use_temporal_edges": use_temporal_edges,
                "include_account_nodes": include_account_nodes,
                **summary,
                "output_root": result["output_root"],
            }
        )

    sweep_frame = pd.DataFrame(sweep_rows).sort_values(
        by=["f1_mean", "pr_auc_mean", "roc_auc_mean"],
        ascending=False,
    )
    output_root = Path(args.output_dir) / f"{dataset_stem}-gnn-sweep"
    output_root.mkdir(parents=True, exist_ok=True)
    sweep_frame.to_csv(output_root / "sweep_results.csv", index=False)
    sweep_frame.to_json(output_root / "sweep_results.json", orient="records", indent=2)
    print(f"Saved sweep results to {output_root}")


if __name__ == "__main__":
    main()
