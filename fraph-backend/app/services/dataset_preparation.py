import json
from datetime import UTC, datetime
from pathlib import Path

from app.services.fraud_detection import run_fraud_detection_from_prepared
from app.services.graph_builder import build_graph_from_prepared
from app.services.preprocessing import preprocess_dataset, recommended_max_rows


def build_preparation_status_path(dataset_path: str | Path) -> Path:
    path = Path(dataset_path)
    return path.with_suffix(f"{path.suffix}.prep.status.json")


def build_preparation_artifact_path(dataset_path: str | Path) -> Path:
    path = Path(dataset_path)
    return path.with_suffix(f"{path.suffix}.prep.artifact.json")


def read_preparation_status(dataset_path: str | Path) -> dict[str, object]:
    status_path = build_preparation_status_path(dataset_path)
    if not status_path.exists():
        return {
            "status": "missing",
            "job_id": None,
            "progress": 0,
            "message": "No preparation job has been started.",
            "updated_at": datetime.now(UTC).isoformat(),
        }
    try:
        return json.loads(status_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {
            "status": "failed",
            "job_id": None,
            "progress": 100,
            "message": "Preparation status file could not be read.",
            "updated_at": datetime.now(UTC).isoformat(),
        }


def write_preparation_status(
    dataset_path: str | Path,
    *,
    status: str,
    message: str,
    job_id: str | None = None,
    progress: int = 0,
    artifact_ready: bool = False,
) -> None:
    payload = {
        "status": status,
        "job_id": job_id,
        "progress": progress,
        "message": message,
        "artifact_ready": artifact_ready,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    build_preparation_status_path(dataset_path).write_text(json.dumps(payload, indent=2))


def save_prepared_analysis_artifact(
    dataset_path: str | Path,
    artifact_payload: dict[str, object],
) -> str:
    artifact_path = build_preparation_artifact_path(dataset_path)
    artifact_path.write_text(json.dumps(artifact_payload, indent=2))
    return str(artifact_path)


def load_prepared_analysis_artifact(dataset_path: str | Path) -> dict[str, object] | None:
    artifact_path = build_preparation_artifact_path(dataset_path)
    if not artifact_path.exists():
        return None
    try:
        return json.loads(artifact_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def prepare_large_dataset_artifact(
    dataset_path: str | Path,
    limit: int = 8,
) -> dict[str, object]:
    prepared, profile = preprocess_dataset(
        str(dataset_path),
        max_rows=recommended_max_rows(dataset_path, purpose="interactive"),
    )
    analysis = run_fraud_detection_from_prepared(
        prepared=prepared,
        profile=profile,
        threshold=0.65,
        limit=limit,
    )
    graph = build_graph_from_prepared(
        prepared,
        limit=limit,
        suspicious_transaction_ids=[
            str(item["transaction_id"]) for item in analysis["suspicious_transactions"]
        ],
    )
    return {
        "status": "completed",
        "summary": analysis["summary"],
        "graph": graph,
        "suspicious_transactions": analysis["suspicious_transactions"],
    }
