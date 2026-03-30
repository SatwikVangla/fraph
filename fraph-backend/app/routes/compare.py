from fastapi import APIRouter

from app.schemas.schema import CompareRequest

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("/")
def compare_models(payload: CompareRequest) -> dict[str, object]:
    return {
        "status": "pending",
        "message": "Model comparison stub",
        "models": payload.model_names,
    }
