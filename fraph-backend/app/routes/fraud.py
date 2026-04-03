from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import DatasetRecord
from app.routes.upload import _dataset_to_response
from app.schemas.schema import FraudAnalysisResponse, FraudCheckRequest
from app.services.dataset_preparation import (
    load_prepared_analysis_artifact,
    read_preparation_status,
)
from app.services.fraud_detection import run_fraud_detection_from_prepared
from app.services.graph_builder import build_graph_from_prepared
from app.services.preprocessing import is_large_dataset, preprocess_dataset, recommended_max_rows

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
    if is_large_dataset(record.stored_path):
        preparation_status = read_preparation_status(record.stored_path)
        artifact_payload = load_prepared_analysis_artifact(record.stored_path)
        if artifact_payload is None or preparation_status.get("status") != "completed":
            raise HTTPException(
                status_code=409,
                detail="Large dataset preprocessing is still running. Wait for the preparation job to complete.",
            )

        return FraudAnalysisResponse(
            status="completed",
            dataset=_dataset_to_response(record),
            summary=artifact_payload["summary"],
            graph=artifact_payload["graph"],
            suspicious_transactions=artifact_payload["suspicious_transactions"],
        )

    prepared, profile = preprocess_dataset(
        record.stored_path,
        max_rows=recommended_max_rows(record.stored_path, purpose="interactive"),
    )
    analysis = run_fraud_detection_from_prepared(
        prepared=prepared,
        profile=profile,
        threshold=payload.threshold,
        limit=payload.limit,
    )
    graph = build_graph_from_prepared(
        prepared,
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
