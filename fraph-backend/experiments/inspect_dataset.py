from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.preprocessing import profile_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a candidate dataset for FRAPH experiment compatibility.",
    )
    parser.add_argument("--dataset", required=True, help="Path to a CSV dataset.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_path = Path(args.dataset).resolve()
    profile = profile_dataset(dataset_path)

    report = {
        "dataset": str(dataset_path),
        "row_count": profile.row_count,
        "columns": profile.columns,
        "detected_columns": {
            "amount": profile.amount_column,
            "sender": profile.sender_column,
            "receiver": profile.receiver_column,
            "label": profile.label_column,
            "transaction_type": profile.transaction_type_column,
            "step": profile.step_column,
            "oldbalance_orig": profile.oldbalance_orig_column,
            "newbalance_orig": profile.newbalance_orig_column,
            "oldbalance_dest": profile.oldbalance_dest_column,
            "newbalance_dest": profile.newbalance_dest_column,
        },
        "compatibility": {
            "dashboard_ready": all(
                [
                    profile.amount_column,
                    profile.sender_column,
                    profile.receiver_column,
                ]
            ),
            "comparison_ready": profile.label_column is not None,
            "paysim_like": all(
                [
                    profile.sender_column,
                    profile.receiver_column,
                    profile.amount_column,
                    profile.transaction_type_column,
                    profile.oldbalance_orig_column,
                    profile.newbalance_orig_column,
                    profile.oldbalance_dest_column,
                    profile.newbalance_dest_column,
                    profile.label_column,
                ]
            ),
        },
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
