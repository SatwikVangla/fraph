import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import DatasetRecord, ModelArtifactRecord
from app.routes.upload import _dataset_to_response
from app.schemas.schema import (
    JobResponse,
    ModelArtifactResponse,
    TrainingRequest,
    TrainingResponse,
)
from app.services.comparison_cache import set_cached_model_result
from app.services.reporting import generate_model_report
from app.services.runtime_jobs import create_job, get_job, start_background_job, update_job
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


def _result_to_response(result: dict[str, object], artifact: ModelArtifactRecord | None = None) -> ModelArtifactResponse:
    return ModelArtifactResponse(
        artifact_id=artifact.id if artifact else None,
        model_name=str(result["model_name"]),
        status=str(result["status"]),
        artifact_path=artifact.artifact_path if artifact else result.get("artifact_path"),
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
        diagnostics=result.get("diagnostics"),
        explainability=result.get("explainability"),
        report_path=result.get("report_path"),
        report_chart_path=result.get("report_chart_path"),
        details=str(result["details"]),
    )


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
                artifact_id=artifact.id,
                model_name=artifact.model_name,
                status=artifact.status,
                artifact_path=artifact.artifact_path,
                accuracy=payload.get("accuracy"),
                precision=payload.get("precision"),
                recall=payload.get("recall"),
                f1_score=payload.get("f1_score"),
                roc_auc=payload.get("roc_auc"),
                pr_auc=payload.get("pr_auc"),
                mcc=payload.get("mcc"),
                tn=payload.get("tn"),
                fp=payload.get("fp"),
                fn=payload.get("fn"),
                tp=payload.get("tp"),
                threshold=payload.get("threshold"),
                validation_score=payload.get("validation_score"),
                tuning_validation_score=payload.get("tuning_validation_score"),
                selected_config=payload.get("selected_config"),
                diagnostics=payload.get("diagnostics"),
                explainability=payload.get("explainability"),
                report_path=payload.get("report_path"),
                report_chart_path=payload.get("report_chart_path"),
                details=str(payload.get("details", "")),
            )
        )
    return results


@router.get("/reports/{artifact_id}")
def download_report(
    artifact_id: int,
    db: Session = Depends(get_db),
):
    artifact = db.query(ModelArtifactRecord).filter(ModelArtifactRecord.id == artifact_id).first()
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    payload = json.loads(artifact.metrics_json or "{}")
    report_path = payload.get("report_path")
    if not report_path:
        raise HTTPException(status_code=404, detail="Report not found for artifact.")
    return FileResponse(report_path, filename=f"{artifact.model_name}-report.md")


@router.post("/jobs", response_model=JobResponse)
def queue_training_job(
    payload: TrainingRequest,
    db: Session = Depends(get_db),
) -> JobResponse:
    dataset = _resolve_dataset(payload, db)
    job_id = create_job(
        "training",
        metadata={
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "model_names": payload.model_names,
        },
    )

    def runner(inner_job_id: str) -> dict[str, object]:
        from app.database.db import SessionLocal

        session = SessionLocal()
        try:
            update_job(inner_job_id, progress=15, message="Preparing training run.")
            requested_models = payload.model_names or [
                "knn",
                "logistic_regression",
                "linear_svc",
                "gaussian_nb",
                "gnn",
            ]
            results: list[dict[str, object]] = []
            classic_models = [model for model in requested_models if model != "gnn"]
            if classic_models:
                update_job(inner_job_id, progress=35, message="Training classical models.")
                results.extend(
                    train_and_persist_models(
                        dataset_path=dataset.stored_path,
                        dataset_name=dataset.name,
                        requested_models=classic_models,
                    )
                )

            if "gnn" in requested_models:
                update_job(inner_job_id, progress=70, message="Training GNN model.")
                results.append(
                    train_gnn_model(
                        dataset_path=dataset.stored_path,
                        dataset_name=dataset.name,
                        epochs=payload.epochs,
                        learning_rate=payload.learning_rate,
                        hidden_dim=payload.hidden_dim,
                        sampling_preset=payload.sampling_preset,
                    )
                )

            response_results: list[dict[str, object]] = []
            for result in results:
                report_paths = generate_model_report(dataset.name, str(result["model_name"]), result)
                result.update(report_paths)
                artifact = _store_artifact(session, dataset.id, result)
                set_cached_model_result(dataset.id, str(result["model_name"]), result)
                response_results.append(_result_to_response(result, artifact).model_dump())

            return {
                "status": "completed",
                "dataset": _dataset_to_response(dataset).model_dump(),
                "training_results": response_results,
            }
        finally:
            session.close()

    start_background_job(job_id, runner)
    job = get_job(job_id)
    assert job is not None
    return JobResponse(**job)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_training_job(job_id: str) -> JobResponse:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobResponse(**job)


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
        "gaussian_nb",
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
                    sampling_preset=payload.sampling_preset,
                )
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    response_results: list[ModelArtifactResponse] = []
    for result in results:
        report_paths = generate_model_report(dataset.name, str(result["model_name"]), result)
        result.update(report_paths)
        artifact = _store_artifact(db, dataset.id, result)
        set_cached_model_result(dataset.id, str(result["model_name"]), result)
        response_results.append(_result_to_response(result, artifact))

    return TrainingResponse(
        status="completed",
        dataset=_dataset_to_response(dataset),
        training_results=response_results,
    )
