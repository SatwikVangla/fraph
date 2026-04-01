import json
from datetime import datetime

from app.database.db import SessionLocal
from app.database.models import ComparisonCacheRecord


def get_cached_model_result(dataset_id: int, model_name: str) -> dict[str, object] | None:
    session = SessionLocal()
    try:
        record = (
            session.query(ComparisonCacheRecord)
            .filter(
                ComparisonCacheRecord.dataset_id == dataset_id,
                ComparisonCacheRecord.model_name == model_name,
            )
            .order_by(ComparisonCacheRecord.updated_at.desc())
            .first()
        )
        return json.loads(record.payload_json) if record is not None else None
    finally:
        session.close()


def set_cached_model_result(dataset_id: int, model_name: str, result: dict[str, object]) -> None:
    session = SessionLocal()
    try:
        record = (
            session.query(ComparisonCacheRecord)
            .filter(
                ComparisonCacheRecord.dataset_id == dataset_id,
                ComparisonCacheRecord.model_name == model_name,
            )
            .first()
        )
        if record is None:
            record = ComparisonCacheRecord(
                dataset_id=dataset_id,
                model_name=model_name,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(record)
        record.payload_json = json.dumps(result)
        record.updated_at = datetime.utcnow()
        session.commit()
    finally:
        session.close()


def list_cached_results(dataset_id: int, requested_models: list[str]) -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    for model_name in requested_models:
        payload = get_cached_model_result(dataset_id, model_name)
        if payload is not None:
            results[model_name] = payload
    return results
