import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

from app.services.diagnostics import build_dataset_diagnostics
from app.services.evaluation import compute_binary_classification_metrics
from app.services.evaluation_splits import build_time_aware_holdout_split
from app.services.fraud_detection import get_numeric_feature_frame
from app.services.gnn_model import (
    build_transaction_graph_from_prepared,
    train_gnn_from_graph,
)
from app.services.preprocessing import preprocess_dataset, recommended_max_rows
from app.utils.helpers import build_model_storage_path

GNN_COMPARE_CONFIG = {
    "epochs": 24,
    "hidden_dim": 192,
    "learning_rate": 0.0013,
    "dropout": 0.1,
    "use_class_weights": True,
    "max_nodes": 1280,
    "seed_candidates": [42],
    "model_architecture": "graphsage",
    "use_similarity_edges": True,
    "use_party_edges": True,
    "use_temporal_edges": True,
    "include_account_nodes": True,
}


def build_linear_svc_model(labels: pd.Series) -> object:
    class_counts = labels.value_counts()
    min_class_count = int(class_counts.min()) if not class_counts.empty else 2
    calibration_folds = max(2, min(3, min_class_count))
    return CalibratedClassifierCV(
        make_pipeline(StandardScaler(), LinearSVC(dual="auto", max_iter=5000)),
        cv=calibration_folds,
    )


def get_model_specs(labels: pd.Series | None = None) -> dict[str, object]:
    fallback_labels = pd.Series([0, 1]) if labels is None else labels
    return {
        "knn": make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=7)),
        "logistic_regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1500, class_weight="balanced"),
        ),
        "linear_svc": build_linear_svc_model(fallback_labels),
        "gaussian_nb": make_pipeline(StandardScaler(), GaussianNB()),
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
    feature_names: list[str] | None = None,
) -> dict[str, object]:
    predictions = model.predict(x_test)
    probabilities = get_model_probabilities(model, x_test)
    metrics = compute_binary_classification_metrics(
        y_true=y_test,
        probabilities=probabilities,
        predictions=predictions,
    )
    explainability: dict[str, object] = {}
    if hasattr(model, "feature_importances_") and feature_names:
        explainability["top_input_features"] = [
            {"feature": name, "importance": round(float(score), 4)}
            for name, score in sorted(
                zip(feature_names, model.feature_importances_),
                key=lambda item: item[1],
                reverse=True,
            )[:10]
        ]
    return {
        "model_name": model_name,
        **metrics,
        "explainability": explainability,
        "status": "completed",
        "details": "Model trained on engineered transaction features.",
    }


def prepare_labeled_dataset(dataset_path: str, purpose: str = "training"):
    prepared, _profile = preprocess_dataset(
        dataset_path,
        max_rows=recommended_max_rows(dataset_path, purpose=purpose),
    )
    if "label" not in prepared.columns or prepared["label"].dropna().empty:
        raise ValueError("Model training requires a labeled fraud column.")

    labeled = prepared.dropna(subset=["label"]).copy().reset_index(drop=True)
    labeled["label"] = labeled["label"].astype(bool)
    if labeled["label"].nunique() < 2 or len(labeled) < 10:
        raise ValueError(
            "Need at least 10 labeled rows with both fraud and non-fraud classes."
        )

    features = get_numeric_feature_frame(labeled)
    labels = labeled["label"].astype(int)
    diagnostics = build_dataset_diagnostics(labeled)
    return labeled, features, labels, diagnostics


def _build_evaluation_strategy(labeled: pd.DataFrame, labels: pd.Series) -> dict[str, object]:
    return build_time_aware_holdout_split(labeled, labels).metadata


def _build_time_aware_split_payload(
    labeled: pd.DataFrame,
    features: pd.DataFrame,
    labels: pd.Series,
) -> tuple[list[int], list[int], pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, dict[str, object]]:
    split = build_time_aware_holdout_split(labeled, labels)
    train_indices = split.train_indices
    test_indices = split.test_indices
    x_train = features.loc[train_indices]
    x_test = features.loc[test_indices]
    y_train = labels.loc[train_indices]
    y_test = labels.loc[test_indices]
    return train_indices, test_indices, x_train, x_test, y_train, y_test, split.metadata


def _attach_evaluation_strategy(result: dict[str, object], evaluation_strategy: dict[str, object]) -> None:
    selected_config = dict(result.get("selected_config") or {})
    selected_config["evaluation_strategy"] = evaluation_strategy
    result["selected_config"] = selected_config


def compare_baseline_models(
    dataset_path: str,
    dataset_name: str | None = None,
    requested_models: list[str] | None = None,
) -> list[dict[str, object]]:
    try:
        labeled, features, labels, diagnostics = prepare_labeled_dataset(
            dataset_path,
            purpose="compare",
        )
    except ValueError as exc:
        return [
            {
                "model_name": "baseline_ml_models",
                "status": "skipped",
                "details": str(exc),
            }
        ]

    train_indices, test_indices, x_train, x_test, y_train, y_test, evaluation_strategy = (
        _build_time_aware_split_payload(labeled, features, labels)
    )

    model_specs = get_model_specs(labels)
    requested = set(requested_models or model_specs.keys())
    unsupported_models = sorted(requested - set(model_specs.keys()))
    results: list[dict[str, object]] = []

    for model_name, model in model_specs.items():
        if model_name not in requested:
            continue

        try:
            model.fit(x_train, y_train)
            metrics = evaluate_model(
                model_name,
                model,
                x_test,
                y_test,
                feature_names=list(features.columns),
            )
            metrics["diagnostics"] = diagnostics
            metrics["details"] = (
                "Model evaluated on a chronological holdout split using engineered transaction "
                "features only."
            )
            _attach_evaluation_strategy(metrics, evaluation_strategy)
            results.append(metrics)
        except Exception as exc:
            results.append(
                {
                    "model_name": model_name,
                    "status": "failed",
                    "diagnostics": diagnostics,
                    "details": f"{model_name} training failed: {exc}",
                }
            )

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
        try:
            graph = build_transaction_graph_from_prepared(
                prepared=labeled,
                train_indices=list(train_indices),
                test_indices=list(test_indices),
                max_nodes=GNN_COMPARE_CONFIG["max_nodes"],
                use_similarity_edges=GNN_COMPARE_CONFIG["use_similarity_edges"],
                use_party_edges=GNN_COMPARE_CONFIG["use_party_edges"],
                use_temporal_edges=GNN_COMPARE_CONFIG["use_temporal_edges"],
                include_account_nodes=GNN_COMPARE_CONFIG["include_account_nodes"],
            )
            gnn_result = train_gnn_from_graph(
                graph=graph,
                dataset_name=dataset_name or "comparison",
                epochs=GNN_COMPARE_CONFIG["epochs"],
                hidden_dim=GNN_COMPARE_CONFIG["hidden_dim"],
                learning_rate=GNN_COMPARE_CONFIG["learning_rate"],
                artifact_name="gnn",
                persist_artifact=False,
                include_raw_outputs=False,
                use_class_weights=GNN_COMPARE_CONFIG["use_class_weights"],
                dropout=GNN_COMPARE_CONFIG["dropout"],
                random_seed=GNN_COMPARE_CONFIG["seed_candidates"][0],
                model_architecture=GNN_COMPARE_CONFIG["model_architecture"],
            )
            gnn_result["selected_config"] = {
                "epochs": GNN_COMPARE_CONFIG["epochs"],
                "hidden_dim": GNN_COMPARE_CONFIG["hidden_dim"],
                "learning_rate": GNN_COMPARE_CONFIG["learning_rate"],
                "dropout": GNN_COMPARE_CONFIG["dropout"],
                "use_similarity_edges": GNN_COMPARE_CONFIG["use_similarity_edges"],
                "use_party_edges": GNN_COMPARE_CONFIG["use_party_edges"],
                "use_temporal_edges": GNN_COMPARE_CONFIG["use_temporal_edges"],
                "include_account_nodes": GNN_COMPARE_CONFIG["include_account_nodes"],
                "model_architecture": GNN_COMPARE_CONFIG["model_architecture"],
                "selected_seed": GNN_COMPARE_CONFIG["seed_candidates"][0],
                "evaluation_strategy": evaluation_strategy,
            }
            gnn_result["details"] = (
                "Stable weighted-message-passing GNN comparison profile on a chronological holdout "
                "split with transaction, party, and temporal graph structure enabled."
            )
            gnn_result["diagnostics"] = diagnostics
            results.append(gnn_result)
        except ValueError as exc:
            results.append(
                {
                    "model_name": "gnn",
                    "status": "skipped",
                    "diagnostics": diagnostics,
                    "details": str(exc),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "model_name": "gnn",
                    "status": "failed",
                    "diagnostics": diagnostics,
                    "details": f"gnn comparison failed: {exc}",
                }
            )

    return results


def train_and_persist_models(
    dataset_path: str,
    dataset_name: str,
    requested_models: list[str] | None = None,
) -> list[dict[str, object]]:
    labeled, features, labels, diagnostics = prepare_labeled_dataset(
        dataset_path,
        purpose="training",
    )

    _train_indices, _test_indices, x_train, x_test, y_train, y_test, evaluation_strategy = (
        _build_time_aware_split_payload(labeled, features, labels)
    )

    model_specs = get_model_specs(labels)
    requested = set(requested_models or model_specs.keys())
    results: list[dict[str, object]] = []

    for model_name, model in model_specs.items():
        if model_name not in requested:
            continue

        try:
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

            metrics = evaluate_model(
                model_name,
                model,
                x_test,
                y_test,
                feature_names=list(features.columns),
            )
            metrics["artifact_path"] = str(artifact_path)
            metrics["diagnostics"] = diagnostics
            metrics["details"] = (
                "Model trained and persisted on engineered transaction features using a "
                "chronological holdout evaluation split."
            )
            _attach_evaluation_strategy(metrics, evaluation_strategy)
            results.append(metrics)
        except Exception as exc:
            results.append(
                {
                    "model_name": model_name,
                    "status": "failed",
                    "artifact_path": None,
                    "diagnostics": diagnostics,
                    "details": f"{model_name} persistence failed: {exc}",
                }
            )

    return results
