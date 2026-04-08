from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException

from app.database.models import DatasetRecord
from app.routes.upload import get_preprocessing_status, list_datasets


def _seed_dataset(test_app: FastAPI) -> DatasetRecord:
    dataset_path = Path(test_app.state.datasets_dir) / "seeded.csv"
    dataset_path.write_text(
        "\n".join(
            [
                "step,type,amount,nameOrig,nameDest,isFraud",
                "1,PAYMENT,100.0,C123,M456,0",
                "2,TRANSFER,325.0,C999,M888,1",
            ]
        )
    )

    session = test_app.state.testing_session_local()
    try:
        record = DatasetRecord(
            name="seeded-dataset",
            original_filename="seeded.csv",
            stored_path=str(dataset_path),
            row_count=2,
            amount_column="amount",
            sender_column="nameOrig",
            receiver_column="nameDest",
            label_column="isFraud",
            created_at=datetime.now(UTC),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        session.expunge(record)
        return record
    finally:
        session.close()


def test_list_datasets_returns_seeded_dataset(test_app: FastAPI) -> None:
    record = _seed_dataset(test_app)

    session = test_app.state.testing_session_local()
    try:
        payload = list_datasets(db=session)
    finally:
        session.close()

    assert len(payload) == 1
    assert payload[0].id == record.id
    assert payload[0].name == "seeded-dataset"
    assert payload[0].file_size_bytes == Path(record.stored_path).stat().st_size
    assert payload[0].large_dataset is False
    assert payload[0].preprocessing_status == "missing"


def test_preprocessing_status_returns_404_for_unknown_dataset(test_app: FastAPI) -> None:
    session = test_app.state.testing_session_local()
    try:
        with pytest.raises(HTTPException) as exc_info:
            get_preprocessing_status(dataset_id=999, db=session)
    finally:
        session.close()

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Dataset not found."
