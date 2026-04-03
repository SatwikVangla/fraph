from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.db import init_db
from app.routes.benchmark import router as benchmark_router
from app.routes.compare import router as compare_router
from app.routes.fraud import router as fraud_router
from app.routes.training import router as training_router
from app.routes.upload import router as upload_router
from app.services.gnn_model import get_training_device_summary
from app.utils.helpers import ensure_runtime_directories


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_runtime_directories()
    init_db()
    device_summary = get_training_device_summary()
    logger.warning("FRAPH training device: %s", device_summary)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(upload_router)
app.include_router(fraud_router)
app.include_router(compare_router)
app.include_router(training_router)
app.include_router(benchmark_router)


@app.get('/')
def read_root() -> dict[str, str]:
    return {'message': f'{settings.app_name} is running'}
