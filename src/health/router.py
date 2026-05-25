# src/health/router.py

from fastapi import APIRouter

from src.health.schemas import HealthResponse
from src.settings.settings import get_settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", name="health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        app_name=settings.app_name,
    )
