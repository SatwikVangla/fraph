from app.routes.compare import router as compare_router
from app.routes.fraud import router as fraud_router
from app.routes.upload import router as upload_router

__all__ = ["upload_router", "fraud_router", "compare_router"]
