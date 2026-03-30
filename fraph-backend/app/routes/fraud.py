from fastapi import APIRouter

from app.schemas.schema import FraudCheckRequest

router = APIRouter(prefix="/fraud", tags=["fraud"])


@router.post("/detect")
def detect_fraud(payload: FraudCheckRequest) -> dict[str, object]:
    return {
        "status": "pending",
        "message": "Fraud detection pipeline stub",
        "transaction_ids": payload.transaction_ids,
    }
