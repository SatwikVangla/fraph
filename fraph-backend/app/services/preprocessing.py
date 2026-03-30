from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class DatasetProfile:
    row_count: int
    columns: list[str]
    amount_column: str | None
    sender_column: str | None
    receiver_column: str | None
    label_column: str | None
    transaction_type_column: str | None
    step_column: str | None
    oldbalance_orig_column: str | None
    newbalance_orig_column: str | None
    oldbalance_dest_column: str | None
    newbalance_dest_column: str | None


COLUMN_ALIASES = {
    "transaction_id": ["transaction_id", "transactionid", "tx_id", "txn_id", "id"],
    "sender": [
        "sender",
        "source",
        "from",
        "from_account",
        "account_id",
        "customer_id",
        "origin",
        "nameorig",
    ],
    "receiver": [
        "receiver",
        "target",
        "to",
        "to_account",
        "merchant",
        "merchant_id",
        "destination",
        "namedest",
    ],
    "amount": ["amount", "transaction_amount", "amt", "value", "transaction_value"],
    "label": ["is_fraud", "fraud", "label", "class", "target_flag", "isfraud"],
    "transaction_type": ["type", "transaction_type", "channel", "payment_type"],
    "step": ["step", "timestamp", "time", "date", "transaction_time"],
    "oldbalance_orig": [
        "oldbalanceorig",
        "oldbalance_org",
        "oldbalanceorigin",
        "oldbalanceorg",
    ],
    "newbalance_orig": ["newbalanceorig", "newbalance_org", "newbalanceorigin"],
    "oldbalance_dest": ["oldbalancedest", "oldbalance_dest"],
    "newbalance_dest": ["newbalancedest", "newbalance_dest"],
}


def _normalize_column_names(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.copy()
    dataframe.columns = [str(column).strip() for column in dataframe.columns]
    return dataframe


def _find_column(columns: list[str], aliases: list[str]) -> str | None:
    lowered = {column.lower(): column for column in columns}
    for alias in aliases:
        if alias in lowered:
            return lowered[alias]
    return None


def _parse_label_value(value: object) -> bool | None:
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "fraud", "fraudulent"}:
        return True
    if normalized in {"0", "false", "no", "legit", "legitimate", "normal"}:
        return False
    return None


def _numeric_series(
    dataframe: pd.DataFrame,
    column_name: str | None,
    default_value: float = 0.0,
) -> pd.Series:
    if column_name is None:
        return pd.Series([default_value] * len(dataframe), index=dataframe.index)
    return pd.to_numeric(dataframe[column_name], errors="coerce").fillna(default_value)


def load_raw_dataset(dataset_path: str | Path) -> pd.DataFrame:
    dataframe = pd.read_csv(dataset_path)
    dataframe = _normalize_column_names(dataframe)
    if dataframe.empty:
        raise ValueError("Dataset is empty.")
    return dataframe


def profile_dataset(dataset_path: str | Path) -> DatasetProfile:
    dataframe = load_raw_dataset(dataset_path)
    columns = list(dataframe.columns)
    amount_column = _find_column(columns, COLUMN_ALIASES["amount"])
    sender_column = _find_column(columns, COLUMN_ALIASES["sender"])
    receiver_column = _find_column(columns, COLUMN_ALIASES["receiver"])
    label_column = _find_column(columns, COLUMN_ALIASES["label"])
    transaction_type_column = _find_column(columns, COLUMN_ALIASES["transaction_type"])
    step_column = _find_column(columns, COLUMN_ALIASES["step"])
    oldbalance_orig_column = _find_column(columns, COLUMN_ALIASES["oldbalance_orig"])
    newbalance_orig_column = _find_column(columns, COLUMN_ALIASES["newbalance_orig"])
    oldbalance_dest_column = _find_column(columns, COLUMN_ALIASES["oldbalance_dest"])
    newbalance_dest_column = _find_column(columns, COLUMN_ALIASES["newbalance_dest"])

    if amount_column is None:
        numeric_columns = dataframe.select_dtypes(include=["number"]).columns.tolist()
        amount_column = numeric_columns[0] if numeric_columns else None

    return DatasetProfile(
        row_count=len(dataframe),
        columns=columns,
        amount_column=amount_column,
        sender_column=sender_column,
        receiver_column=receiver_column,
        label_column=label_column,
        transaction_type_column=transaction_type_column,
        step_column=step_column,
        oldbalance_orig_column=oldbalance_orig_column,
        newbalance_orig_column=newbalance_orig_column,
        oldbalance_dest_column=oldbalance_dest_column,
        newbalance_dest_column=newbalance_dest_column,
    )


def preprocess_dataset(dataset_path: str | Path) -> tuple[pd.DataFrame, DatasetProfile]:
    dataframe = load_raw_dataset(dataset_path)
    profile = profile_dataset(dataset_path)

    transaction_id_column = _find_column(
        list(dataframe.columns),
        COLUMN_ALIASES["transaction_id"],
    )

    if transaction_id_column:
        transaction_ids = dataframe[transaction_id_column].astype(str)
    else:
        transaction_ids = pd.Series(
            [f"txn-{index + 1}" for index in range(len(dataframe))],
            index=dataframe.index,
        )

    if profile.sender_column:
        sender = dataframe[profile.sender_column].fillna("unknown_sender").astype(str)
    else:
        sender = pd.Series(["unknown_sender"] * len(dataframe), index=dataframe.index)

    if profile.receiver_column:
        receiver = dataframe[profile.receiver_column].fillna("unknown_receiver").astype(str)
    else:
        receiver = pd.Series(["unknown_receiver"] * len(dataframe), index=dataframe.index)

    if profile.transaction_type_column:
        transaction_type = (
            dataframe[profile.transaction_type_column].fillna("unknown").astype(str)
        )
    else:
        transaction_type = pd.Series(["unknown"] * len(dataframe), index=dataframe.index)

    amount = _numeric_series(dataframe, profile.amount_column, default_value=0.0).astype(
        float
    )
    step = _numeric_series(
        dataframe,
        profile.step_column,
        default_value=0.0,
    ).astype(float)
    oldbalance_orig = _numeric_series(dataframe, profile.oldbalance_orig_column).astype(
        float
    )
    newbalance_orig = _numeric_series(dataframe, profile.newbalance_orig_column).astype(
        float
    )
    oldbalance_dest = _numeric_series(dataframe, profile.oldbalance_dest_column).astype(
        float
    )
    newbalance_dest = _numeric_series(dataframe, profile.newbalance_dest_column).astype(
        float
    )

    labels = None
    if profile.label_column:
        labels = dataframe[profile.label_column].map(_parse_label_value)

    prepared = pd.DataFrame(
        {
            "transaction_id": transaction_ids,
            "sender": sender,
            "receiver": receiver,
            "transaction_type": transaction_type,
            "step": step,
            "amount": amount,
            "oldbalance_orig": oldbalance_orig,
            "newbalance_orig": newbalance_orig,
            "oldbalance_dest": oldbalance_dest,
            "newbalance_dest": newbalance_dest,
            "balance_delta_orig": newbalance_orig - oldbalance_orig,
            "balance_delta_dest": newbalance_dest - oldbalance_dest,
        }
    )

    if labels is not None:
        prepared["label"] = labels

    return prepared, profile
