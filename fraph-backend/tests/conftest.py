import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.database.models import Base
import importlib

upload_routes = importlib.import_module('app.routes.upload')
upload_router = upload_routes.router


@pytest.fixture
def test_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[FastAPI, None, None]:
    database_path = tmp_path / 'test.db'
    engine = create_engine(
        f'sqlite:///{database_path}',
        connect_args={'check_same_thread': False},
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)

    datasets_dir = tmp_path / 'datasets'
    datasets_dir.mkdir(parents=True, exist_ok=True)

    def override_get_db() -> Generator[Session, None, None]:
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    def test_storage_path(filename: str) -> Path:
        return datasets_dir / filename

    monkeypatch.setattr(upload_routes, 'ensure_runtime_directories', lambda: None)
    monkeypatch.setattr(upload_routes, 'build_dataset_storage_path', test_storage_path)

    app = FastAPI()
    app.include_router(upload_router)
    app.dependency_overrides[upload_routes.get_db] = override_get_db
    app.state.testing_session_local = testing_session_local
    app.state.datasets_dir = datasets_dir

    yield app

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
