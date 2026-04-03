import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import DatasetRecord, ModelArtifactRecord
from app.routes.upload import _dataset_to_response
from app.schemas.schema import CompareRequest, CompareResponse, ModelMetric
from app.services.comparison_cache import list_cached_results, set_cached_model_result
from app.services.diagnostics import build_dataset_diagnostics
from app.services.ml_models import compare_baseline_models
from app.services.preprocessing import preprocess_dataset

router = APIRouter(prefix="/compare", tags=["compare"])


def _has_material_metrics(result: dict[str, object]) -> bool:
    return any(
        result.get(metric_name) is not None
        for metric_name in ("accuracy", "precision", "recall", "f1_score", "roc_auc")
    )


def _resolve_dataset(payload: CompareRequest, db: Session) -> DatasetRecord:
    query = db.query(DatasetRecord)
    record = None
    if payload.dataset_id is not None:
        record = query.filter(DatasetRecord.id == payload.dataset_id).first()
    elif payload.dataset_name:
        record = query.filter(DatasetRecord.name == payload.dataset_name).first()

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found. Upload a dataset first.",
        )
    return record


def _load_artifact_metrics(artifact: ModelArtifactRecord | None) -> dict[str, object] | None:
    if artifact is None or not artifact.metrics_json:
        return None

    payload = json.loads(artifact.metrics_json)
    if not isinstance(payload, dict):
        return None
    return payload


@router.post("/", response_model=CompareResponse)
def compare_models(
    payload: CompareRequest,
    db: Session = Depends(get_db),
) -> CompareResponse:
    record = _resolve_dataset(payload, db)
    requested_models = payload.model_names or [
        "knn",
        "logistic_regression",
        "linear_svc",
        "gaussian_nb",
        "gnn",
    ]
    cached_results = list_cached_results(record.id, requested_models)
    artifact_records = (
        db.query(ModelArtifactRecord)
        .filter(ModelArtifactRecord.dataset_id == record.id)
        .order_by(ModelArtifactRecord.created_at.desc())
        .all()
    )
    latest_artifacts: dict[str, ModelArtifactRecord] = {}
    artifact_payloads: dict[str, dict[str, object]] = {}
    for artifact in artifact_records:
        latest_artifacts.setdefault(artifact.model_name, artifact)

    for model_name, artifact in latest_artifacts.items():
        payload_metrics = _load_artifact_metrics(artifact)
        if payload_metrics is not None:
            artifact_payloads[model_name] = payload_metrics

    missing_models = [
        model_name
        for model_name in requested_models
        if not _has_material_metrics(cached_results.get(model_name, {}))
        and not _has_material_metrics(artifact_payloads.get(model_name, {}))
    ]
    if missing_models:
        comparison_results = compare_baseline_models(
            dataset_path=record.stored_path,
            dataset_name=record.name,
            requested_models=missing_models,
        )
        for result in comparison_results:
            result_model_name = str(result.get("model_name", ""))
            if result_model_name not in missing_models:
                continue
            cached_results[result_model_name] = result
            if _has_material_metrics(result):
                set_cached_model_result(record.id, result_model_name, result)

    prepared, _profile = preprocess_dataset(record.stored_path)
    diagnostics = build_dataset_diagnostics(prepared)

    merged_results: list[ModelMetric] = []
    for model_name in requested_models:
        result = cached_results.get(model_name)
        artifact = latest_artifacts.get(model_name)
        if result is not None and _has_material_metrics(result):
            merged_results.append(
                ModelMetric(
                    model_name=model_name,
                    accuracy=result.get("accuracy"),
                    precision=result.get("precision"),
                    recall=result.get("recall"),
                    f1_score=result.get("f1_score"),
                    roc_auc=result.get("roc_auc"),
                    pr_auc=result.get("pr_auc"),
                    mcc=result.get("mcc"),
                    tn=result.get("tn"),
                    fp=result.get("fp"),
                    fn=result.get("fn"),
                    tp=result.get("tp"),
                    threshold=result.get("threshold"),
                    validation_score=result.get("validation_score"),
                    tuning_validation_score=result.get("tuning_validation_score"),
                    selected_config=result.get("selected_config"),
                    diagnostics=result.get("diagnostics") or diagnostics,
                    explainability=result.get("explainability"),
                    status=str(result["status"]),
                    details=str(result["details"]),
                )
            )
            continue

        payload_metrics = artifact_payloads.get(model_name)
        if artifact and payload_metrics and _has_material_metrics(payload_metrics):
            merged_results.append(
                ModelMetric(
                    model_name=artifact.model_name,
                    accuracy=payload_metrics.get("accuracy"),
                    precision=payload_metrics.get("precision"),
                    recall=payload_metrics.get("recall"),
                    f1_score=payload_metrics.get("f1_score"),
                    roc_auc=payload_metrics.get("roc_auc"),
                    pr_auc=payload_metrics.get("pr_auc"),
                    mcc=payload_metrics.get("mcc"),
                    tn=payload_metrics.get("tn"),
                    fp=payload_metrics.get("fp"),
                    fn=payload_metrics.get("fn"),
                    tp=payload_metrics.get("tp"),
                    threshold=payload_metrics.get("threshold"),
                    validation_score=payload_metrics.get("validation_score"),
                    tuning_validation_score=payload_metrics.get("tuning_validation_score"),
                    selected_config=payload_metrics.get("selected_config"),
                    diagnostics=payload_metrics.get("diagnostics") or diagnostics,
                    explainability=payload_metrics.get("explainability"),
                    status=artifact.status,
                    details=str(
                        payload_metrics.get(
                            "details",
                            "Model metrics loaded from saved artifact.",
                        )
                    ),
                )
            )
            continue

        merged_results.append(
            ModelMetric(
                model_name=model_name,
                diagnostics=diagnostics,
                status="missing",
                details="No saved artifact or cached result is available yet.",
            )
        )

    return CompareResponse(
        status="completed",
        dataset=_dataset_to_response(record),
        diagnostics=diagnostics,
        model_results=merged_results,
    )
