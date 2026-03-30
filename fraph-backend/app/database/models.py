from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DatasetRecord(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(500), unique=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    amount_column: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_column: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receiver_column: Mapped[str | None] = mapped_column(String(255), nullable=True)
    label_column: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=datetime.utcnow,
    )


class ModelArtifactRecord(Base):
    __tablename__ = "model_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True)
    model_name: Mapped[str] = mapped_column(String(255), index=True)
    artifact_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    metrics_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=datetime.utcnow,
    )
