from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import DatasetRecord
from app.routes.upload import _dataset_to_response
from app.schemas.schema import FraudAnalysisResponse, FraudCheckRequest
from app.services.fraud_detection import run_fraud_detection
from app.services.graph_builder import build_graph

router = APIRouter(prefix="/fraud", tags=["fraud"])


def _resolve_dataset(
    payload: FraudCheckRequest,
    db: Session,
) -> DatasetRecord:
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


@router.post("/detect", response_model=FraudAnalysisResponse)
def detect_fraud(
    payload: FraudCheckRequest,
    db: Session = Depends(get_db),
) -> FraudAnalysisResponse:
    record = _resolve_dataset(payload, db)
    analysis = run_fraud_detection(
        dataset_path=record.stored_path,
        threshold=payload.threshold,
        limit=payload.limit,
    )
    graph = build_graph(
        record.stored_path,
        limit=payload.limit,
        suspicious_transaction_ids=[
            str(item["transaction_id"]) for item in analysis["suspicious_transactions"]
        ],
    )

    return FraudAnalysisResponse(
        status="completed",
        dataset=_dataset_to_response(record),
        summary=analysis["summary"],
        graph=graph,
        suspicious_transactions=analysis["suspicious_transactions"],
    )
