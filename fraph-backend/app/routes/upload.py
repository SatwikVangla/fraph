from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/")
async def upload_dataset(file: UploadFile = File(...)) -> dict[str, str]:
    return {
        "filename": file.filename or "",
        "content_type": file.content_type or "application/octet-stream",
        "status": "received",
    }
