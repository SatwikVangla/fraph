from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import DatasetRecord
from app.schemas.schema import DatasetResponse, JobResponse, UploadDatasetResponse
from app.services.dataset_preparation import (
    prepare_large_dataset_artifact,
    read_preparation_status,
    save_prepared_analysis_artifact,
    write_preparation_status,
)
from app.services.preprocessing import (
    MAX_UPLOAD_BYTES,
    LARGE_DATASET_BYTES,
    dataset_file_size_bytes,
    is_large_dataset,
    profile_dataset,
    save_mapping_overrides,
)
from app.services.runtime_jobs import create_job, get_job, start_background_job, update_job
from app.utils.helpers import build_dataset_storage_path, ensure_runtime_directories, slugify_name

router = APIRouter(prefix="/upload", tags=["upload"])
UPLOAD_CHUNK_SIZE = 1024 * 1024


def _dataset_to_response(record: DatasetRecord) -> DatasetResponse:
    file_size_bytes = dataset_file_size_bytes(record.stored_path)
    preparation_status = read_preparation_status(record.stored_path)
    return DatasetResponse(
        id=record.id,
        name=record.name,
        original_filename=record.original_filename,
        stored_path=record.stored_path,
        row_count=record.row_count,
        file_size_bytes=file_size_bytes,
        large_dataset=file_size_bytes >= LARGE_DATASET_BYTES,
        preprocessing_status=str(preparation_status.get("status")),
        preprocessing_job_id=preparation_status.get("job_id"),
        amount_column=record.amount_column,
        sender_column=record.sender_column,
        receiver_column=record.receiver_column,
        label_column=record.label_column,
        created_at=record.created_at,
    )


@router.get("/datasets", response_model=list[DatasetResponse])
def list_datasets(db: Session = Depends(get_db)) -> list[DatasetResponse]:
    records = db.query(DatasetRecord).order_by(DatasetRecord.created_at.desc()).all()
    return [_dataset_to_response(record) for record in records]


@router.get("/preprocessing-status/{dataset_id}", response_model=JobResponse)
def get_preprocessing_status(
    dataset_id: int,
    db: Session = Depends(get_db),
) -> JobResponse:
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    preparation_status = read_preparation_status(record.stored_path)
    job_id = preparation_status.get("job_id")
    if job_id:
        job = get_job(str(job_id))
        if job is not None:
            return JobResponse(**job)

    return JobResponse(
        job_id=str(job_id or f"dataset-{dataset_id}-preprocessing"),
        job_type="dataset_preprocessing",
        status=str(preparation_status.get("status", "missing")),
        progress=int(preparation_status.get("progress", 0)),
        message=str(preparation_status.get("message", "No preprocessing status available.")),
        error=None,
        result=None,
        metadata={"dataset_id": dataset_id},
        created_at=str(preparation_status.get("updated_at")),
        updated_at=str(preparation_status.get("updated_at")),
    )


@router.post("/", response_model=UploadDatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    amount_column: str | None = Form(default=None),
    sender_column: str | None = Form(default=None),
    receiver_column: str | None = Form(default=None),
    label_column: str | None = Form(default=None),
    transaction_type_column: str | None = Form(default=None),
    step_column: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> UploadDatasetResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A CSV file is required.")

    extension = Path(file.filename).suffix.lower()
    if extension != ".csv":
        raise HTTPException(status_code=400, detail="Only CSV uploads are supported.")

    ensure_runtime_directories()
    stored_path = build_dataset_storage_path(file.filename)

    total_bytes = 0
    with stored_path.open("wb") as handle:
        while True:
            chunk = await file.read(UPLOAD_CHUNK_SIZE)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > MAX_UPLOAD_BYTES:
                handle.close()
                stored_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail="CSV is too large. The current upload limit is 1 GB.",
                )
            handle.write(chunk)

    try:
        mapping_overrides = {
            "amount_column": amount_column,
            "sender_column": sender_column,
            "receiver_column": receiver_column,
            "label_column": label_column,
            "transaction_type_column": transaction_type_column,
            "step_column": step_column,
        }
        if any(value for value in mapping_overrides.values()):
            save_mapping_overrides(stored_path, mapping_overrides)
        profile = profile_dataset(stored_path)
    except Exception as exc:  # noqa: BLE001
        stored_path.unlink(missing_ok=True)
        stored_path.with_suffix(f"{stored_path.suffix}.mapping.json").unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse dataset: {exc}",
        ) from exc

    base_dataset_name = slugify_name(Path(file.filename).stem)
    dataset_name = base_dataset_name
    suffix = 1
    while db.query(DatasetRecord).filter(DatasetRecord.name == dataset_name).first():
        suffix += 1
        dataset_name = f"{base_dataset_name}-{suffix}"

    record = DatasetRecord(
        name=dataset_name,
        original_filename=file.filename,
        stored_path=str(stored_path),
        row_count=profile.row_count,
        amount_column=profile.amount_column,
        sender_column=profile.sender_column,
        receiver_column=profile.receiver_column,
        label_column=profile.label_column,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    if is_large_dataset(stored_path):
        job_id = create_job(
            "dataset_preprocessing",
            metadata={"dataset_id": record.id, "dataset_name": record.name},
        )
        write_preparation_status(
            stored_path,
            status="queued",
            message="Large dataset preprocessing queued.",
            job_id=job_id,
            progress=0,
        )

        def runner(inner_job_id: str) -> dict[str, object]:
            write_preparation_status(
                stored_path,
                status="running",
                message="Preparing sampled analysis artifact for large dataset.",
                job_id=inner_job_id,
                progress=15,
            )
            update_job(
                inner_job_id,
                progress=15,
                message="Preparing sampled analysis artifact for large dataset.",
            )
            artifact_payload = prepare_large_dataset_artifact(stored_path, limit=8)
            artifact_path = save_prepared_analysis_artifact(stored_path, artifact_payload)
            write_preparation_status(
                stored_path,
                status="completed",
                message="Large dataset artifact is ready.",
                job_id=inner_job_id,
                progress=100,
                artifact_ready=True,
            )
            return {
                "dataset_id": record.id,
                "dataset_name": record.name,
                "artifact_path": artifact_path,
            }

        start_background_job(job_id, runner)

    return UploadDatasetResponse(
        status="completed",
        message=(
            "Dataset uploaded and indexed successfully."
            if total_bytes < LARGE_DATASET_BYTES
            else "Large dataset uploaded successfully. Interactive analysis will use sampled rows to keep the app responsive."
        ),
        dataset=_dataset_to_response(record),
    )
