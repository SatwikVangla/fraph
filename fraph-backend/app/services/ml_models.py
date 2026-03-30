import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

from app.services.evaluation import compute_binary_classification_metrics
from app.services.fraud_detection import get_numeric_feature_frame
from app.services.gnn_model import get_gnn_comparison_result
from app.services.preprocessing import preprocess_dataset
from app.utils.helpers import build_model_storage_path


def get_model_specs() -> dict[str, object]:
    return {
        "knn": make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=7)),
        "logistic_regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000),
        ),
        "linear_svc": CalibratedClassifierCV(
            make_pipeline(StandardScaler(), LinearSVC(dual="auto", max_iter=5000)),
            cv=3,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            class_weight="balanced",
        ),
    }


def get_model_probabilities(model, x_test) -> list[float] | pd.Series:
    if hasattr(model, "predict_proba"):
        return model.predict_proba(x_test)[:, 1]

    decision_values = model.decision_function(x_test)
    min_score = float(decision_values.min())
    max_score = float(decision_values.max())
    if max_score == min_score:
        return [0.0] * len(decision_values)
    return [
        (float(value) - min_score) / (max_score - min_score)
        for value in decision_values
    ]


def evaluate_model(
    model_name: str,
    model,
    x_test,
    y_test,
) -> dict[str, object]:
    predictions = model.predict(x_test)
    probabilities = get_model_probabilities(model, x_test)
    metrics = compute_binary_classification_metrics(
        y_true=y_test,
        probabilities=probabilities,
        predictions=predictions,
    )
    return {
        "model_name": model_name,
        **metrics,
        "status": "completed",
        "details": "Model trained on engineered transaction features.",
    }


def prepare_labeled_dataset(dataset_path: str):
    prepared, _profile = preprocess_dataset(dataset_path)
    if "label" not in prepared.columns or prepared["label"].dropna().empty:
        raise ValueError("Model training requires a labeled fraud column.")

    labeled = prepared.dropna(subset=["label"]).copy()
    labeled["label"] = labeled["label"].astype(bool)
    if labeled["label"].nunique() < 2 or len(labeled) < 10:
        raise ValueError(
            "Need at least 10 labeled rows with both fraud and non-fraud classes."
        )

    features = get_numeric_feature_frame(labeled)
    labels = labeled["label"].astype(int)
    return labeled, features, labels


def compare_baseline_models(
    dataset_path: str,
    requested_models: list[str] | None = None,
) -> list[dict[str, object]]:
    try:
        _labeled, features, labels = prepare_labeled_dataset(dataset_path)
    except ValueError as exc:
        return [
            {
                "model_name": "baseline_ml_models",
                "status": "skipped",
                "details": str(exc),
            }
        ]

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.25,
        random_state=42,
        stratify=labels,
    )

    requested = set(requested_models or get_model_specs().keys())
    unsupported_models = sorted(requested - set(get_model_specs().keys()))
    results: list[dict[str, object]] = []

    for model_name, model in get_model_specs().items():
        if model_name not in requested:
            continue

        model.fit(x_train, y_train)
        results.append(evaluate_model(model_name, model, x_test, y_test))

    include_gnn_result = not requested_models or "gnn" in requested
    for unsupported_model in unsupported_models:
        if unsupported_model == "gnn":
            include_gnn_result = True
            continue
        results.append(
            {
                "model_name": unsupported_model,
                "status": "skipped",
                "details": "Requested model is not implemented yet.",
            }
        )

    if include_gnn_result:
        results.append(get_gnn_comparison_result())

    return results


def train_and_persist_models(
    dataset_path: str,
    dataset_name: str,
    requested_models: list[str] | None = None,
) -> list[dict[str, object]]:
    labeled, features, labels = prepare_labeled_dataset(dataset_path)

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.25,
        random_state=42,
        stratify=labels,
    )

    requested = set(requested_models or get_model_specs().keys())
    results: list[dict[str, object]] = []

    for model_name, model in get_model_specs().items():
        if model_name not in requested:
            continue

        model.fit(x_train, y_train)
        artifact_path = build_model_storage_path(dataset_name, model_name, ".joblib")
        joblib.dump(
            {
                "model": model,
                "feature_columns": list(features.columns),
                "row_count": int(len(labeled)),
            },
            artifact_path,
        )

        metrics = evaluate_model(model_name, model, x_test, y_test)
        metrics["artifact_path"] = str(artifact_path)
        metrics["details"] = (
            "Model trained and persisted on engineered transaction features."
        )
        results.append(metrics)

    return results
