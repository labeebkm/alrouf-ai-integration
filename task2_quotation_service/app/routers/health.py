"""Health check endpoint."""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health", summary="Service health check")
async def health():
    return {
        "status": "ok",
        "service": "AL ROUF Quotation Microservice",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
