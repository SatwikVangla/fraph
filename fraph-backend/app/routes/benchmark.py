import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import SessionLocal, get_db
from app.database.models import DatasetRecord, ExperimentRunRecord
from app.routes.training import _resolve_dataset
from app.schemas.schema import BenchmarkRequest, ExperimentRunResponse, JobResponse
from app.services.runtime_jobs import create_job, get_job, start_background_job, update_job
from experiments.run_benchmark import run_benchmark

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


def _experiment_to_response(record: ExperimentRunRecord) -> ExperimentRunResponse:
    return ExperimentRunResponse(
        experiment_id=record.id,
        dataset_id=record.dataset_id,
        run_type=record.run_type,
        status=record.status,
        output_root=record.output_root,
        summary=json.loads(record.summary_json or "{}"),
        config=json.loads(record.config_json or "{}"),
        created_at=record.created_at,
    )


@router.get("/runs/{dataset_id}", response_model=list[ExperimentRunResponse])
def list_benchmark_runs(
    dataset_id: int,
    db: Session = Depends(get_db),
) -> list[ExperimentRunResponse]:
    runs = (
        db.query(ExperimentRunRecord)
        .filter(ExperimentRunRecord.dataset_id == dataset_id)
        .order_by(ExperimentRunRecord.created_at.desc())
        .all()
    )
    return [_experiment_to_response(run) for run in runs]


@router.post("/jobs", response_model=JobResponse)
def queue_benchmark_job(
    payload: BenchmarkRequest,
    db: Session = Depends(get_db),
) -> JobResponse:
    dataset = _resolve_dataset(payload, db)
    job_id = create_job(
        "benchmark",
        metadata={
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
        },
    )

    def runner(inner_job_id: str) -> dict[str, object]:
        session = SessionLocal()
        try:
            experiment = ExperimentRunRecord(
                dataset_id=dataset.id,
                run_type="benchmark",
                status="running",
            )
            session.add(experiment)
            session.commit()
            session.refresh(experiment)

            update_job(inner_job_id, progress=15, message="Running benchmark splits.")
            result = run_benchmark(
                dataset=dataset.stored_path,
                models=payload.model_names or [
                    "knn",
                    "logistic_regression",
                    "linear_svc",
                    "gaussian_nb",
                    "gnn",
                    "gnn_graphsage",
                    "gnn_gat",
                ],
                folds=payload.folds,
                repeats=payload.repeats,
                seed=payload.seed,
                gnn_epochs=payload.gnn_epochs,
                gnn_hidden_dim=payload.gnn_hidden_dim,
                gnn_learning_rate=payload.gnn_learning_rate,
                gnn_dropout=payload.gnn_dropout,
                output_dir="outputs",
                output_suffix=f"dataset-{dataset.id}",
            )

            summary = result["summary"].to_dict(orient="records")
            experiment.status = "completed"
            experiment.output_root = str(result["output_root"])
            experiment.summary_json = json.dumps(summary)
            experiment.config_json = json.dumps(
                {
                    "dataset_id": dataset.id,
                    "dataset_name": dataset.name,
                    "models": payload.model_names,
                    "folds": payload.folds,
                    "repeats": payload.repeats,
                    "seed": payload.seed,
                    "gnn_epochs": payload.gnn_epochs,
                    "gnn_hidden_dim": payload.gnn_hidden_dim,
                }
            )
            session.commit()
            session.refresh(experiment)
            return _experiment_to_response(experiment).model_dump()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    start_background_job(job_id, runner)
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=500, detail="Failed to initialize benchmark job.")
    return JobResponse(**job)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_benchmark_job(job_id: str) -> JobResponse:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobResponse(**job)
