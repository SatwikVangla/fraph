import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import DatasetRecord, ModelArtifactRecord
from app.routes.upload import _dataset_to_response
from app.schemas.schema import (
    ModelArtifactResponse,
    TrainingRequest,
    TrainingResponse,
)
from app.services.gnn_model import train_gnn_model
from app.services.ml_models import train_and_persist_models

router = APIRouter(prefix="/train", tags=["training"])


def _resolve_dataset(payload: TrainingRequest, db: Session) -> DatasetRecord:
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


def _store_artifact(
    db: Session,
    dataset_id: int,
    result: dict[str, object],
) -> ModelArtifactRecord:
    artifact = (
        db.query(ModelArtifactRecord)
        .filter(
            ModelArtifactRecord.dataset_id == dataset_id,
            ModelArtifactRecord.model_name == str(result["model_name"]),
        )
        .first()
    )
    if artifact is None:
        artifact = ModelArtifactRecord(
            dataset_id=dataset_id,
            model_name=str(result["model_name"]),
        )
        db.add(artifact)

    artifact.artifact_path = (
        str(result["artifact_path"]) if result.get("artifact_path") else None
    )
    artifact.status = str(result["status"])
    artifact.metrics_json = json.dumps(result)
    db.commit()
    db.refresh(artifact)
    return artifact


@router.get("/artifacts/{dataset_id}", response_model=list[ModelArtifactResponse])
def list_artifacts(
    dataset_id: int,
    db: Session = Depends(get_db),
) -> list[ModelArtifactResponse]:
    artifacts = (
        db.query(ModelArtifactRecord)
        .filter(ModelArtifactRecord.dataset_id == dataset_id)
        .order_by(ModelArtifactRecord.created_at.desc())
        .all()
    )
    results: list[ModelArtifactResponse] = []
    for artifact in artifacts:
        payload = json.loads(artifact.metrics_json or "{}")
        results.append(
            ModelArtifactResponse(
                model_name=artifact.model_name,
                status=artifact.status,
                artifact_path=artifact.artifact_path,
                accuracy=payload.get("accuracy"),
                precision=payload.get("precision"),
                recall=payload.get("recall"),
                f1_score=payload.get("f1_score"),
                roc_auc=payload.get("roc_auc"),
                details=str(payload.get("details", "")),
            )
        )
    return results


@router.post("/", response_model=TrainingResponse)
def train_models(
    payload: TrainingRequest,
    db: Session = Depends(get_db),
) -> TrainingResponse:
    dataset = _resolve_dataset(payload, db)
    requested_models = payload.model_names or [
        "knn",
        "logistic_regression",
        "linear_svc",
        "random_forest",
        "gnn",
    ]

    results: list[dict[str, object]] = []
    classic_models = [model for model in requested_models if model != "gnn"]

    if classic_models:
        try:
            results.extend(
                train_and_persist_models(
                    dataset_path=dataset.stored_path,
                    dataset_name=dataset.name,
                    requested_models=classic_models,
                )
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    if "gnn" in requested_models:
        try:
            results.append(
                train_gnn_model(
                    dataset_path=dataset.stored_path,
                    dataset_name=dataset.name,
                    epochs=payload.epochs,
                    learning_rate=payload.learning_rate,
                    hidden_dim=payload.hidden_dim,
                )
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    response_results: list[ModelArtifactResponse] = []
    for result in results:
        artifact = _store_artifact(db, dataset.id, result)
        response_results.append(
            ModelArtifactResponse(
                model_name=str(result["model_name"]),
                status=str(result["status"]),
                artifact_path=artifact.artifact_path,
                accuracy=result.get("accuracy"),
                precision=result.get("precision"),
                recall=result.get("recall"),
                f1_score=result.get("f1_score"),
                roc_auc=result.get("roc_auc"),
                details=str(result["details"]),
            )
        )

    return TrainingResponse(
        status="completed",
        dataset=_dataset_to_response(dataset),
        training_results=response_results,
    )
