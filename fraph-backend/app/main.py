from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.db import init_db
from app.routes import benchmark_router, compare_router, fraud_router, training_router, upload_router
from app.utils.helpers import ensure_runtime_directories


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_runtime_directories()
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(fraud_router)
app.include_router(compare_router)
app.include_router(training_router)
app.include_router(benchmark_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": f"{settings.app_name} is running"}
