from datetime import datetime

from pydantic import BaseModel, Field


class FraudCheckRequest(BaseModel):
    dataset_id: int | None = None
    dataset_name: str | None = None
    threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    limit: int = Field(default=10, ge=1, le=100)


class CompareRequest(BaseModel):
    dataset_id: int | None = None
    model_names: list[str] = Field(default_factory=list)
    dataset_name: str | None = None


class TrainingRequest(BaseModel):
    dataset_id: int | None = None
    dataset_name: str | None = None
    model_names: list[str] = Field(default_factory=list)
    epochs: int = Field(default=80, ge=5, le=500)
    learning_rate: float = Field(default=0.005, gt=0.0, le=1.0)
    hidden_dim: int = Field(default=64, ge=4, le=512)


class DatasetResponse(BaseModel):
    id: int
    name: str
    original_filename: str
    stored_path: str
    row_count: int
    amount_column: str | None = None
    sender_column: str | None = None
    receiver_column: str | None = None
    label_column: str | None = None
    created_at: datetime


class UploadDatasetResponse(BaseModel):
    status: str
    message: str
    dataset: DatasetResponse


class SuspiciousTransaction(BaseModel):
    transaction_id: str
    sender: str
    receiver: str
    amount: float
    risk_score: float
    predicted_fraud: bool
    actual_label: bool | None = None


class GraphNode(BaseModel):
    id: str
    label: str
    degree: int
    total_amount: float


class GraphEdge(BaseModel):
    source: str
    target: str
    count: int
    total_amount: float


class FraudSummary(BaseModel):
    transactions_analyzed: int
    suspicious_transactions: int
    fraud_rate: float
    average_risk_score: float
    total_amount: float


class GraphSummary(BaseModel):
    node_count: int
    edge_count: int
    connected_components: int
    density: float
    top_nodes: list[GraphNode] = Field(default_factory=list)
    top_edges: list[GraphEdge] = Field(default_factory=list)


class FraudAnalysisResponse(BaseModel):
    status: str
    dataset: DatasetResponse
    summary: FraudSummary
    graph: GraphSummary
    suspicious_transactions: list[SuspiciousTransaction]


class ModelMetric(BaseModel):
    model_name: str
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1_score: float | None = None
    roc_auc: float | None = None
    status: str
    details: str


class CompareResponse(BaseModel):
    status: str
    dataset: DatasetResponse
    model_results: list[ModelMetric] = Field(default_factory=list)


class ModelArtifactResponse(BaseModel):
    model_name: str
    status: str
    artifact_path: str | None = None
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1_score: float | None = None
    roc_auc: float | None = None
    details: str


class TrainingResponse(BaseModel):
    status: str
    dataset: DatasetResponse
    training_results: list[ModelArtifactResponse] = Field(default_factory=list)
