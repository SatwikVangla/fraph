from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import DatasetRecord
from app.routes.upload import _dataset_to_response
from app.schemas.schema import CompareRequest, CompareResponse
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

    return CompareResponse(
        status="completed",
        dataset=_dataset_to_response(record),
        model_results=model_results,
    )
