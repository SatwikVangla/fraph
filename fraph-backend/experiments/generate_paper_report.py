from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate paper-ready result tables.")
    parser.add_argument("--summary", required=True, help="Path to summary_metrics.csv")
    parser.add_argument(
        "--output",
        default="paper_report",
        help="Output directory for generated report files.",
    )
    return parser.parse_args()


def to_latex_table(frame: pd.DataFrame) -> str:
    headers = frame.columns.tolist()
    lines = [
        "\\begin{tabular}{" + "l" * len(headers) + "}",
        "\\hline",
        " & ".join(headers) + " \\\\",
        "\\hline",
    ]
    for row in frame.astype(str).values.tolist():
        lines.append(" & ".join(row) + " \\\\")
    lines.extend(["\\hline", "\\end{tabular}"])
    return "\n".join(lines) + "\n"


def to_markdown_table(frame: pd.DataFrame) -> str:
    headers = frame.columns.tolist()
    separator = ["---"] * len(headers)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in frame.astype(str).values.tolist())
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    summary_path = Path(args.summary).resolve()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = pd.read_csv(summary_path)
    ranked = summary.sort_values(
        by=["f1_mean", "pr_auc_mean", "roc_auc_mean"],
        ascending=False,
    ).reset_index(drop=True)
    ranked.to_csv(output_dir / "ranked_summary.csv", index=False)

    paper_table = ranked[
        [
            "model_name",
            "precision_mean",
            "recall_mean",
            "f1_mean",
            "roc_auc_mean",
            "pr_auc_mean",
            "mcc_mean",
        ]
    ].copy()
    paper_table.columns = [
        "Model",
        "Precision",
        "Recall",
        "F1",
        "ROC-AUC",
        "PR-AUC",
        "MCC",
    ]
    paper_table.to_csv(output_dir / "paper_table.csv", index=False)

    markdown_lines = [
        "# Paper Results Report",
        "",
        "## Ranked Models",
        "",
        to_markdown_table(paper_table),
        "",
        "## Best Model",
        "",
        f"- Best by F1: `{ranked.iloc[0]['model_name']}`",
    ]
    (output_dir / "paper_report.md").write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")
    (output_dir / "paper_table.tex").write_text(to_latex_table(paper_table), encoding="utf-8")
    print(f"Saved paper report to {output_dir}")


if __name__ == "__main__":
    main()
