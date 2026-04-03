import json
import socket
import threading
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

import uvicorn
from fastapi import FastAPI

from app.database.models import DatasetRecord


def _seed_dataset(test_app: FastAPI) -> DatasetRecord:
    dataset_path = Path(test_app.state.datasets_dir) / 'seeded.csv'
    dataset_path.write_text(
        '\n'.join(
            [
                'step,type,amount,nameOrig,nameDest,isFraud',
                '1,PAYMENT,100.0,C123,M456,0',
                '2,TRANSFER,325.0,C999,M888,1',
            ]
        )
    )

    session = test_app.state.testing_session_local()
    try:
        record = DatasetRecord(
            name='seeded-dataset',
            original_filename='seeded.csv',
            stored_path=str(dataset_path),
            row_count=2,
            amount_column='amount',
            sender_column='nameOrig',
            receiver_column='nameDest',
            label_column='isFraud',
            created_at=datetime.now(UTC),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        session.expunge(record)
        return record
    finally:
        session.close()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


@contextmanager
def _serve_app(test_app: FastAPI):
    port = _free_port()
    config = uvicorn.Config(test_app, host='127.0.0.1', port=port, log_level='error')
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 5
    base_url = f'http://127.0.0.1:{port}'
    while time.time() < deadline:
        try:
            urlopen(f'{base_url}/openapi.json', timeout=0.2).read()
            break
        except OSError:
            time.sleep(0.05)
    else:
        server.should_exit = True
        thread.join(timeout=2)
        raise RuntimeError('Test server did not start in time.')

    try:
        yield base_url
    finally:
        server.should_exit = True
        thread.join(timeout=5)


def _read_json(url: str) -> tuple[int, object]:
    try:
        with urlopen(url, timeout=2) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except HTTPError as error:
        return error.code, json.loads(error.read().decode('utf-8'))


def test_list_datasets_returns_seeded_dataset(test_app: FastAPI) -> None:
    record = _seed_dataset(test_app)

    with _serve_app(test_app) as base_url:
        status_code, payload = _read_json(f'{base_url}/upload/datasets')

    assert status_code == 200
    assert len(payload) == 1
    assert payload[0]['id'] == record.id
    assert payload[0]['name'] == 'seeded-dataset'
    assert payload[0]['file_size_bytes'] == Path(record.stored_path).stat().st_size
    assert payload[0]['large_dataset'] is False
    assert payload[0]['preprocessing_status'] == 'missing'


def test_preprocessing_status_returns_404_for_unknown_dataset(test_app: FastAPI) -> None:
    with _serve_app(test_app) as base_url:
        status_code, payload = _read_json(f'{base_url}/upload/preprocessing-status/999')

    assert status_code == 404
    assert payload['detail'] == 'Dataset not found.'
