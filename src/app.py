# src/app.py
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ── STARTUP ──────────────────
    logger.info("Application starting up")

    yield  # ← application is running and serving requests

    # ── SHUTDOWN ─────────────────
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="CollabTask",
        version="0.0.1",
        description="A production-grade REST + WebSocket API for a multi-tenant task management platform.",
        lifespan=lifespan,
    )
    return app


app = create_app()
