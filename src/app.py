# src/app.py
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from src.database.engine import dispose_db, init_db
from src.settings.settings import get_settings
from src.shared.connection_manager import dispose_cm, init_cm
from src.shared.router import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ── STARTUP ──────────────────
    logger.info("Application starting up")
    init_db(app)
    init_cm(app)

    yield  # ← application is running and serving requests

    # ── SHUTDOWN ─────────────────
    logger.info("Application shutting down")
    await dispose_db(app)
    await dispose_cm(app)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A production-grade REST + WebSocket API for a multi-tenant task management platform.",
        lifespan=lifespan,
    )
    app.include_router(api_router)
    return app


app = create_app()
