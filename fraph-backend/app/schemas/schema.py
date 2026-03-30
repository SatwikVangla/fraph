from pydantic import BaseModel, Field


class FraudCheckRequest(BaseModel):
    transaction_ids: list[str] = Field(default_factory=list)
    dataset_name: str | None = None


class CompareRequest(BaseModel):
    model_names: list[str] = Field(default_factory=list)
    dataset_name: str | None = None
