from fastapi import FastAPI

from app.routes import compare_router, fraud_router, upload_router

app = FastAPI(title="Fraph Backend")

app.include_router(upload_router)
app.include_router(fraud_router)
app.include_router(compare_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Fraph backend is running"}
