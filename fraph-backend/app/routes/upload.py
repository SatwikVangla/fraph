from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import DatasetRecord
from app.schemas.schema import DatasetResponse, UploadDatasetResponse
from app.services.preprocessing import profile_dataset
from app.utils.helpers import build_dataset_storage_path, ensure_runtime_directories, slugify_name

router = APIRouter(prefix="/upload", tags=["upload"])


def _dataset_to_response(record: DatasetRecord) -> DatasetResponse:
    return DatasetResponse(
        id=record.id,
        name=record.name,
        original_filename=record.original_filename,
        stored_path=record.stored_path,
        row_count=record.row_count,
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


@router.post("/", response_model=UploadDatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> UploadDatasetResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A CSV file is required.")

    extension = Path(file.filename).suffix.lower()
    if extension != ".csv":
        raise HTTPException(status_code=400, detail="Only CSV uploads are supported.")

    ensure_runtime_directories()
    stored_path = build_dataset_storage_path(file.filename)

    content = await file.read()
    stored_path.write_bytes(content)

    try:
        profile = profile_dataset(stored_path)
    except Exception as exc:  # noqa: BLE001
        stored_path.unlink(missing_ok=True)
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

    return UploadDatasetResponse(
        status="completed",
        message="Dataset uploaded and indexed successfully.",
        dataset=_dataset_to_response(record),
    )
