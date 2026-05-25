# src/shared/router.py
from fastapi import APIRouter

from src.health.router import router as health_router

# V1 router
v1_router = APIRouter(prefix="/v1")
v1_router.include_router(health_router)

# API router
api_router = APIRouter(prefix="/api")
api_router.include_router(v1_router)
