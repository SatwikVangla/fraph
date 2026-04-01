import pandas as pd


def _build_leakage_audit(prepared: pd.DataFrame) -> dict[str, object]:
    if "label" not in prepared.columns or prepared["label"].dropna().empty:
        return {"status": "unavailable", "warnings": ["No labels available for leakage audit."]}

    labeled = prepared.dropna(subset=["label"]).copy()
    labeled["label"] = labeled["label"].astype(int)
    warnings: list[str] = []
    suspicious_features: list[dict[str, object]] = []

    for column in [
        "oldbalance_orig",
        "newbalance_orig",
        "oldbalance_dest",
        "newbalance_dest",
        "balance_delta_orig",
        "balance_delta_dest",
        "amount",
        "step",
    ]:
        if column not in labeled.columns:
            continue
        numeric = pd.to_numeric(labeled[column], errors="coerce").fillna(0.0)
        if numeric.nunique() <= 1:
            continue
        correlation = abs(float(numeric.corr(labeled["label"])))
        if correlation >= 0.8:
            warnings.append(f"{column} is highly correlated with the label ({correlation:.3f}).")
        suspicious_features.append(
            {
                "feature": column,
                "label_correlation": round(correlation, 4),
                "unique_values": int(numeric.nunique()),
            }
        )

    suspicious_features.sort(key=lambda item: item["label_correlation"], reverse=True)
    return {
        "status": "completed",
        "warnings": warnings,
        "top_label_correlations": suspicious_features[:8],
    }


def build_dataset_diagnostics(prepared: pd.DataFrame) -> dict[str, object]:
    labeled = prepared.dropna(subset=["label"]).copy() if "label" in prepared.columns else prepared.iloc[0:0].copy()
    total_rows = int(len(prepared))
    labeled_rows = int(len(labeled))
    positive_count = int(labeled["label"].astype(int).sum()) if labeled_rows else 0
    negative_count = labeled_rows - positive_count
    fraud_ratio = round(positive_count / labeled_rows, 4) if labeled_rows else None
    duplicate_transactions = int(prepared["transaction_id"].duplicated().sum()) if "transaction_id" in prepared.columns else 0
    self_loops = int((prepared["sender"].astype(str) == prepared["receiver"].astype(str)).sum())
    missing_value_count = int(prepared.isna().sum().sum())
    warnings: list[str] = []

    if labeled_rows == 0:
        warnings.append("Dataset has no parsed fraud labels.")
    if labeled_rows and positive_count < 10:
        warnings.append("Positive fraud examples are very limited; model metrics may be unstable.")
    if fraud_ratio is not None and fraud_ratio < 0.02:
        warnings.append("Fraud rate is extremely imbalanced; prefer PR-AUC, recall, and MCC over accuracy.")
    if duplicate_transactions > 0:
        warnings.append("Duplicate transaction identifiers detected.")
    if missing_value_count > 0:
        warnings.append("Missing values detected and filled during preprocessing.")
    if self_loops > max(5, int(total_rows * 0.05)):
        warnings.append("High self-loop volume detected; inspect sender/receiver mapping quality.")

    return {
        "row_count": total_rows,
        "labeled_row_count": labeled_rows,
        "class_distribution": {
            "fraud": positive_count,
            "legitimate": negative_count,
            "fraud_ratio": fraud_ratio,
        },
        "duplicate_transactions": duplicate_transactions,
        "self_loops": self_loops,
        "missing_value_count": missing_value_count,
        "warnings": warnings,
        "leakage_audit": _build_leakage_audit(prepared),
    }
