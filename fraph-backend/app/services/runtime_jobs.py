import json
from datetime import datetime
from threading import Thread
from uuid import uuid4

from app.database.db import SessionLocal
from app.database.models import JobRecord


def create_job(job_type: str, metadata: dict[str, object] | None = None) -> str:
    job_id = str(uuid4())
    session = SessionLocal()
    try:
        session.add(
            JobRecord(
                id=job_id,
                job_type=job_type,
                status="queued",
                progress=0,
                message="Job queued.",
                result_json="null",
                metadata_json=json.dumps(metadata or {}),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        session.commit()
    finally:
        session.close()
    return job_id


def update_job(job_id: str, **changes: object) -> None:
    session = SessionLocal()
    try:
        job = session.get(JobRecord, job_id)
        if job is None:
            raise KeyError(job_id)
        if "status" in changes:
            job.status = str(changes["status"])
        if "progress" in changes:
            job.progress = int(changes["progress"])
        if "message" in changes:
            job.message = str(changes["message"])
        if "error" in changes:
            job.error = None if changes["error"] is None else str(changes["error"])
        if "result" in changes:
            job.result_json = json.dumps(changes["result"])
        if "metadata" in changes:
            job.metadata_json = json.dumps(changes["metadata"])
        job.updated_at = datetime.utcnow()
        session.commit()
    finally:
        session.close()


def get_job(job_id: str) -> dict[str, object] | None:
    session = SessionLocal()
    try:
        job = session.get(JobRecord, job_id)
        if job is None:
            return None
        return {
            "job_id": job.id,
            "job_type": job.job_type,
            "status": job.status,
            "progress": job.progress,
            "message": job.message,
            "error": job.error,
            "result": json.loads(job.result_json or "null"),
            "metadata": json.loads(job.metadata_json or "{}"),
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
        }
    finally:
        session.close()


def start_background_job(job_id: str, fn) -> None:
    def runner() -> None:
        try:
            update_job(job_id, status="running", progress=5, message="Job started.")
            result = fn(job_id)
            update_job(job_id, status="completed", progress=100, message="Job completed.", result=result)
        except Exception as exc:
            update_job(job_id, status="failed", progress=100, message="Job failed.", error=str(exc))

    Thread(target=runner, daemon=True).start()
