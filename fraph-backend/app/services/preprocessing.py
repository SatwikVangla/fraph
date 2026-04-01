import json
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
    "transaction_id": [
        "transaction_id",
        "transactionid",
        "tx_id",
        "txn_id",
        "id",
        "reference",
        "reference_id",
        "payment_id",
        "order_id",
    ],
    "sender": [
        "sender",
        "source",
        "src",
        "from",
        "from_account",
        "fromaccount",
        "sender_id",
        "origin_account",
        "origin_user",
        "account_id",
        "customer_id",
        "user_id",
        "origin",
        "nameorig",
    ],
    "receiver": [
        "receiver",
        "target",
        "dst",
        "to",
        "to_account",
        "toaccount",
        "receiver_id",
        "beneficiary",
        "payee",
        "destination_account",
        "merchant",
        "merchant_id",
        "destination",
        "namedest",
    ],
    "amount": [
        "amount",
        "transaction_amount",
        "amt",
        "value",
        "transaction_value",
        "payment_amount",
        "debit_amount",
        "credit_amount",
    ],
    "label": [
        "is_fraud",
        "fraud",
        "label",
        "class",
        "target_flag",
        "isfraud",
        "target",
        "y",
        "anomaly",
    ],
    "transaction_type": [
        "type",
        "transaction_type",
        "channel",
        "payment_type",
        "mode",
        "event_type",
    ],
    "step": ["step", "timestamp", "time", "date", "transaction_time", "event_time"],
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


def _canonicalize_name(value: str) -> str:
    return "".join(character for character in str(value).lower() if character.isalnum())


def _normalize_column_names(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.copy()
    dataframe.columns = [str(column).strip() for column in dataframe.columns]
    return dataframe


def build_mapping_sidecar_path(dataset_path: str | Path) -> Path:
    path = Path(dataset_path)
    return path.with_suffix(f"{path.suffix}.mapping.json")


def load_mapping_overrides(dataset_path: str | Path) -> dict[str, str]:
    sidecar_path = build_mapping_sidecar_path(dataset_path)
    if not sidecar_path.exists():
        return {}

    try:
        payload = json.loads(sidecar_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(payload, dict):
        return {}

    return {
        str(key): str(value)
        for key, value in payload.items()
        if value is not None and str(value).strip()
    }


def save_mapping_overrides(dataset_path: str | Path, mappings: dict[str, str]) -> None:
    sidecar_path = build_mapping_sidecar_path(dataset_path)
    cleaned = {
        str(key): str(value)
        for key, value in mappings.items()
        if value is not None and str(value).strip()
    }
    sidecar_path.write_text(json.dumps(cleaned, indent=2, sort_keys=True))


def _find_column(columns: list[str], aliases: list[str]) -> str | None:
    lowered = {_canonicalize_name(column): column for column in columns}
    for alias in aliases:
        normalized_alias = _canonicalize_name(alias)
        if normalized_alias in lowered:
            return lowered[normalized_alias]
    return None


def _find_keyword_column(
    dataframe: pd.DataFrame,
    keywords: list[str],
    *,
    exclude: set[str] | None = None,
    prefer_numeric: bool | None = None,
) -> str | None:
    excluded = exclude or set()
    candidates: list[tuple[int, str]] = []
    for column in dataframe.columns:
        if column in excluded:
            continue
        normalized = _canonicalize_name(column)
        if prefer_numeric is True and not pd.api.types.is_numeric_dtype(dataframe[column]):
            continue
        if prefer_numeric is False and pd.api.types.is_numeric_dtype(dataframe[column]):
            continue

        score = 0
        for keyword in keywords:
            if keyword in normalized:
                score += len(keyword)
        if score > 0:
            candidates.append((score, column))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _infer_amount_column(dataframe: pd.DataFrame, exclude: set[str]) -> str | None:
    keyword_match = _find_keyword_column(
        dataframe,
        ["amount", "amt", "value", "payment", "debit", "credit", "money"],
        exclude=exclude,
        prefer_numeric=True,
    )
    if keyword_match:
        return keyword_match

    numeric_columns = [
        column
        for column in dataframe.select_dtypes(include=["number"]).columns
        if column not in exclude
    ]
    if not numeric_columns:
        return None

    ranked = sorted(
        numeric_columns,
        key=lambda column: (
            float(pd.to_numeric(dataframe[column], errors="coerce").abs().mean()),
            float(pd.to_numeric(dataframe[column], errors="coerce").nunique()),
        ),
        reverse=True,
    )
    return ranked[0]


def _infer_entity_column(
    dataframe: pd.DataFrame,
    keywords: list[str],
    exclude: set[str],
) -> str | None:
    keyword_match = _find_keyword_column(
        dataframe,
        keywords,
        exclude=exclude,
        prefer_numeric=False,
    )
    if keyword_match:
        return keyword_match

    object_columns = [
        column
        for column in dataframe.columns
        if column not in exclude and not pd.api.types.is_numeric_dtype(dataframe[column])
    ]
    if not object_columns:
        return None

    ranked = sorted(
        object_columns,
        key=lambda column: dataframe[column].astype(str).nunique(),
        reverse=True,
    )
    return ranked[0]


def _infer_step_column(dataframe: pd.DataFrame, exclude: set[str]) -> str | None:
    keyword_match = _find_keyword_column(
        dataframe,
        ["time", "timestamp", "date", "step", "event", "created", "occurred"],
        exclude=exclude,
    )
    if keyword_match:
        return keyword_match

    for column in dataframe.columns:
        if column in exclude:
            continue
        parsed = pd.to_datetime(dataframe[column], errors="coerce")
        if parsed.notna().mean() >= 0.7:
            return column

    return None


def _infer_label_column(dataframe: pd.DataFrame, exclude: set[str]) -> str | None:
    keyword_match = _find_keyword_column(
        dataframe,
        ["fraud", "label", "class", "target", "anomaly"],
        exclude=exclude,
    )
    if keyword_match:
        return keyword_match

    for column in dataframe.columns:
        if column in exclude:
            continue
        unique_values = dataframe[column].dropna().astype(str).str.lower().unique().tolist()
        if 1 < len(unique_values) <= 4 and set(unique_values).issubset(
            {"0", "1", "true", "false", "yes", "no", "fraud", "legit", "normal"}
        ):
            return column
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
    dataframe = pd.read_csv(dataset_path, sep=None, engine="python")
    dataframe = _normalize_column_names(dataframe)
    if dataframe.empty:
        raise ValueError("Dataset is empty.")
    return dataframe


def profile_dataset(dataset_path: str | Path) -> DatasetProfile:
    dataframe = load_raw_dataset(dataset_path)
    columns = list(dataframe.columns)
    overrides = load_mapping_overrides(dataset_path)
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
        amount_column = _infer_amount_column(dataframe, exclude=set())

    reserved_columns = {
        column_name
        for column_name in [
            amount_column,
            label_column,
            transaction_type_column,
            step_column,
            oldbalance_orig_column,
            newbalance_orig_column,
            oldbalance_dest_column,
            newbalance_dest_column,
        ]
        if column_name
    }

    if sender_column is None:
        sender_column = _infer_entity_column(
            dataframe,
            keywords=["sender", "source", "origin", "from", "payer", "customer", "user", "account"],
            exclude=reserved_columns,
        )
    if sender_column:
        reserved_columns.add(sender_column)

    if receiver_column is None:
        receiver_column = _infer_entity_column(
            dataframe,
            keywords=[
                "receiver",
                "target",
                "destination",
                "to",
                "merchant",
                "beneficiary",
                "payee",
                "account",
            ],
            exclude=reserved_columns,
        )
    if receiver_column:
        reserved_columns.add(receiver_column)

    if label_column is None:
        label_column = _infer_label_column(dataframe, exclude=reserved_columns)
    if step_column is None:
        step_column = _infer_step_column(dataframe, exclude=reserved_columns)

    amount_column = overrides.get("amount_column", amount_column)
    sender_column = overrides.get("sender_column", sender_column)
    receiver_column = overrides.get("receiver_column", receiver_column)
    label_column = overrides.get("label_column", label_column)
    transaction_type_column = overrides.get(
        "transaction_type_column",
        transaction_type_column,
    )
    step_column = overrides.get("step_column", step_column)

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
    if profile.step_column:
        parsed_step = pd.to_datetime(dataframe[profile.step_column], errors="coerce")
        if parsed_step.notna().mean() >= 0.7:
            step = (
                (parsed_step - parsed_step.min()).dt.total_seconds().fillna(0.0).astype(float)
            )
        else:
            step = _numeric_series(
                dataframe,
                profile.step_column,
                default_value=0.0,
            ).astype(float)
    else:
        step = pd.Series(range(len(dataframe)), index=dataframe.index, dtype=float)
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
