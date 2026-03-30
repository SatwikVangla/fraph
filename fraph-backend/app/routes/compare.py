import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import DatasetRecord, ModelArtifactRecord
from app.routes.upload import _dataset_to_response
from app.schemas.schema import CompareRequest, CompareResponse, ModelMetric
from app.services.ml_models import compare_baseline_models

router = APIRouter(prefix="/compare", tags=["compare"])


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


@router.post("/", response_model=CompareResponse)
def compare_models(
    payload: CompareRequest,
    db: Session = Depends(get_db),
) -> CompareResponse:
    record = _resolve_dataset(payload, db)
    model_results = compare_baseline_models(
        dataset_path=record.stored_path,
        dataset_name=record.name,
        requested_models=payload.model_names,
    )
    artifact_records = (
        db.query(ModelArtifactRecord)
        .filter(ModelArtifactRecord.dataset_id == record.id)
        .order_by(ModelArtifactRecord.created_at.desc())
        .all()
    )
    latest_artifacts: dict[str, ModelArtifactRecord] = {}
    for artifact in artifact_records:
        latest_artifacts.setdefault(artifact.model_name, artifact)

    merged_results: list[ModelMetric] = []
    for result in model_results:
        artifact = latest_artifacts.get(str(result["model_name"]))
        if artifact and artifact.metrics_json:
            payload_metrics = json.loads(artifact.metrics_json)
            merged_results.append(
                ModelMetric(
                    model_name=artifact.model_name,
                    accuracy=payload_metrics.get("accuracy"),
                    precision=payload_metrics.get("precision"),
                    recall=payload_metrics.get("recall"),
                    f1_score=payload_metrics.get("f1_score"),
                    roc_auc=payload_metrics.get("roc_auc"),
                    status=artifact.status,
                    details=str(
                        payload_metrics.get(
                            "details",
                            result.get("details", "Model metrics loaded from saved artifact."),
                        )
                    ),
                )
            )
            continue

        merged_results.append(
            ModelMetric(
                model_name=str(result["model_name"]),
                accuracy=result.get("accuracy"),
                precision=result.get("precision"),
                recall=result.get("recall"),
                f1_score=result.get("f1_score"),
                roc_auc=result.get("roc_auc"),
                status=str(result["status"]),
                details=str(result["details"]),
            )
        )

    return CompareResponse(
        status="completed",
        dataset=_dataset_to_response(record),
        model_results=merged_results,
    )
