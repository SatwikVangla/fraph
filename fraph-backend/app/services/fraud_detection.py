import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.services.preprocessing import preprocess_dataset


def build_feature_frame(dataframe: pd.DataFrame) -> pd.DataFrame:
    features = dataframe.copy()

    sender_counts = features.groupby("sender")["transaction_id"].transform("count")
    receiver_counts = features.groupby("receiver")["transaction_id"].transform("count")
    pair_counts = (
        features.groupby(["sender", "receiver"])["transaction_id"].transform("count")
    )

    amount = features["amount"].fillna(0.0).astype(float)
    step_value = pd.to_numeric(features["step"], errors="coerce").fillna(0.0)
    sender_group = features.groupby("sender", sort=False)
    receiver_group = features.groupby("receiver", sort=False)
    pair_group = features.groupby(["sender", "receiver"], sort=False)

    features["amount_log"] = np.log1p(np.abs(amount))
    features["sender_tx_count"] = sender_counts
    features["receiver_tx_count"] = receiver_counts
    features["pair_tx_count"] = pair_counts
    features["self_loop"] = (features["sender"] == features["receiver"]).astype(int)
    features["transaction_type_code"] = pd.factorize(
        features["transaction_type"].fillna("unknown").astype(str)
    )[0]
    features["step_value"] = step_value
    features["origin_balance_shift"] = (
        pd.to_numeric(features["balance_delta_orig"], errors="coerce")
        .fillna(0.0)
        .abs()
    )
    features["destination_balance_shift"] = (
        pd.to_numeric(features["balance_delta_dest"], errors="coerce")
        .fillna(0.0)
        .abs()
    )
    features["amount_to_origin_balance"] = amount / (
        pd.to_numeric(features["oldbalance_orig"], errors="coerce").fillna(0.0) + 1.0
    )
    features["amount_to_destination_balance"] = amount / (
        pd.to_numeric(features["oldbalance_dest"], errors="coerce").fillna(0.0) + 1.0
    )
    features["sender_unique_receivers"] = sender_group["receiver"].transform("nunique").astype(float)
    features["receiver_unique_senders"] = receiver_group["sender"].transform("nunique").astype(float)
    features["sender_total_sent_amount"] = sender_group["amount"].transform("sum").astype(float)
    features["receiver_total_received_amount"] = (
        receiver_group["amount"].transform("sum").astype(float)
    )
    features["sender_mean_amount"] = sender_group["amount"].transform("mean").astype(float)
    features["receiver_mean_amount"] = receiver_group["amount"].transform("mean").astype(float)
    features["pair_total_amount"] = pair_group["amount"].transform("sum").astype(float)
    features["pair_mean_amount"] = pair_group["amount"].transform("mean").astype(float)
    features["pair_density"] = pair_counts / sender_counts.clip(lower=1.0)
    features["sender_activity_ratio"] = sender_counts / receiver_counts.clip(lower=1.0)
    features["receiver_activity_ratio"] = receiver_counts / sender_counts.clip(lower=1.0)
    features["amount_vs_sender_mean"] = amount / features["sender_mean_amount"].replace(0.0, 1.0)
    features["amount_vs_receiver_mean"] = (
        amount / features["receiver_mean_amount"].replace(0.0, 1.0)
    )
    features["amount_vs_pair_mean"] = amount / features["pair_mean_amount"].replace(0.0, 1.0)
    features["sender_step_mean"] = sender_group["step"].transform("mean").astype(float)
    features["receiver_step_mean"] = receiver_group["step"].transform("mean").astype(float)
    features["step_from_sender_mean"] = (step_value - features["sender_step_mean"]).abs()
    features["step_from_receiver_mean"] = (step_value - features["receiver_step_mean"]).abs()
    features["pair_step_rank"] = pair_group.cumcount().astype(float)
    features["sender_step_rank"] = sender_group.cumcount().astype(float)
    features["receiver_step_rank"] = receiver_group.cumcount().astype(float)
    features["counterparty_diversity"] = (
        features["sender_unique_receivers"] + features["receiver_unique_senders"]
    )
    features["account_net_flow"] = (
        features["sender_total_sent_amount"] - features["receiver_total_received_amount"]
    )
    features["pair_time_gap"] = pair_group["step"].diff().abs().fillna(0.0).astype(float)
    features["sender_time_gap"] = sender_group["step"].diff().abs().fillna(0.0).astype(float)
    features["receiver_time_gap"] = receiver_group["step"].diff().abs().fillna(0.0).astype(float)
    features["pair_is_burst"] = (features["pair_time_gap"] <= 1.0).astype(float)
    features["sender_is_burst"] = (features["sender_time_gap"] <= 1.0).astype(float)
    features["receiver_is_burst"] = (features["receiver_time_gap"] <= 1.0).astype(float)
    features["step_percentile"] = step_value.rank(method="average", pct=True).astype(float)
    features["amount_step_interaction"] = amount * (1.0 + features["step_percentile"])
    features["balance_shift_total"] = (
        features["origin_balance_shift"] + features["destination_balance_shift"]
    )
    features["balance_gap_ratio"] = features["balance_shift_total"] / (amount.abs() + 1.0)
    features["is_cashout_like"] = (
        features["transaction_type"].fillna("").astype(str).str.lower().isin({"cash_out", "cashout"})
    ).astype(int)
    features["is_transfer_like"] = (
        features["transaction_type"].fillna("").astype(str).str.lower().isin({"transfer", "payment"})
    ).astype(int)

    return features


def get_numeric_feature_frame(dataframe: pd.DataFrame) -> pd.DataFrame:
    features = build_feature_frame(dataframe)
    numeric_columns = [
        "amount_log",
        "sender_tx_count",
        "receiver_tx_count",
        "pair_tx_count",
        "self_loop",
        "transaction_type_code",
        "step_value",
        "origin_balance_shift",
        "destination_balance_shift",
        "amount_to_origin_balance",
        "amount_to_destination_balance",
        "sender_unique_receivers",
        "receiver_unique_senders",
        "sender_total_sent_amount",
        "receiver_total_received_amount",
        "sender_mean_amount",
        "receiver_mean_amount",
        "pair_total_amount",
        "pair_mean_amount",
        "pair_density",
        "sender_activity_ratio",
        "receiver_activity_ratio",
        "amount_vs_sender_mean",
        "amount_vs_receiver_mean",
        "amount_vs_pair_mean",
        "sender_step_mean",
        "receiver_step_mean",
        "step_from_sender_mean",
        "step_from_receiver_mean",
        "pair_step_rank",
        "sender_step_rank",
        "receiver_step_rank",
        "counterparty_diversity",
        "account_net_flow",
        "pair_time_gap",
        "sender_time_gap",
        "receiver_time_gap",
        "pair_is_burst",
        "sender_is_burst",
        "receiver_is_burst",
        "step_percentile",
        "amount_step_interaction",
        "balance_shift_total",
        "balance_gap_ratio",
        "is_cashout_like",
        "is_transfer_like",
    ]
    numeric = features[numeric_columns].copy()
    return numeric.replace([np.inf, -np.inf], 0.0).fillna(0.0)


def _normalize_series(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce").fillna(0.0).astype(float)
    max_value = numeric.max()
    min_value = numeric.min()
    if max_value == min_value:
        return pd.Series([0.0] * len(numeric), index=numeric.index)
    return (numeric - min_value) / (max_value - min_value)


def run_fraud_detection(
    dataset_path: str,
    threshold: float = 0.65,
    limit: int = 10,
) -> dict[str, object]:
    prepared, profile = preprocess_dataset(dataset_path)
    features = build_feature_frame(prepared)
    numeric_features = get_numeric_feature_frame(prepared)

    amount_component = _normalize_series(features["amount_log"])
    sender_component = _normalize_series(features["sender_tx_count"])
    receiver_component = _normalize_series(features["receiver_tx_count"])
    pair_component = _normalize_series(features["pair_tx_count"])
    balance_component = _normalize_series(
        features["origin_balance_shift"] + features["destination_balance_shift"]
    )
    self_loop_component = features["self_loop"].astype(float)

    heuristic_score = (
        amount_component * 0.25
        + sender_component * 0.15
        + receiver_component * 0.10
        + pair_component * 0.15
        + balance_component * 0.20
        + self_loop_component * 0.15
    )

    risk_score = heuristic_score
    if len(features) >= 20:
        detector = IsolationForest(
            contamination=min(max(1.0 / len(features), 0.03), 0.15),
            n_estimators=200,
            random_state=42,
        )
        detector.fit(numeric_features)
        anomaly_score = -detector.score_samples(numeric_features)
        anomaly_component = _normalize_series(pd.Series(anomaly_score))
        risk_score = heuristic_score * 0.55 + anomaly_component * 0.45

    results = prepared.copy()
    results["risk_score"] = risk_score.round(4)
    results["predicted_fraud"] = results["risk_score"] >= threshold

    if "label" in prepared.columns:
        results["actual_label"] = prepared["label"]
    else:
        results["actual_label"] = None

    suspicious = (
        results.sort_values("risk_score", ascending=False)
        .head(limit)
        .to_dict(orient="records")
    )

    suspicious_transactions = [
        {
            "transaction_id": str(row["transaction_id"]),
            "sender": str(row["sender"]),
            "receiver": str(row["receiver"]),
            "amount": round(float(row["amount"]), 2),
            "risk_score": round(float(row["risk_score"]), 4),
            "predicted_fraud": bool(row["predicted_fraud"]),
            "actual_label": (
                bool(row["actual_label"])
                if row["actual_label"] is not None
                else None
            ),
        }
        for row in suspicious
    ]

    suspicious_count = int(results["predicted_fraud"].sum())
    fraud_rate = suspicious_count / len(results) if len(results) else 0.0
    average_risk = float(results["risk_score"].mean()) if len(results) else 0.0
    total_amount = float(results["amount"].sum()) if len(results) else 0.0

    return {
        "status": "completed",
        "profile": profile,
        "summary": {
            "transactions_analyzed": int(len(results)),
            "suspicious_transactions": suspicious_count,
            "fraud_rate": round(fraud_rate, 4),
            "average_risk_score": round(average_risk, 4),
            "total_amount": round(total_amount, 2),
        },
        "suspicious_transactions": suspicious_transactions,
    }
