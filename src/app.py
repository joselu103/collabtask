# src/app.py
from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import FastAPI

from src.database.engine import dispose_db, init_db
from src.settings.settings import get_settings
from src.shared.connection_manager import dispose_cm, init_cm
from src.shared.exceptions import register_exception_handlers
from src.shared.limiter import init_limiter
from src.shared.logging_config import configure_logging
from src.shared.middleware import RequestIDMiddleware
from src.shared.router import api_router
from src.workers.arq_app import dispose_arq_pool, init_arq_pool

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ── STARTUP ──────────────────
    await logger.ainfo("Application starting up")
    init_db(app)
    init_cm(app)
    await init_arq_pool(app)

    yield  # ← application is running and serving requests

    # ── SHUTDOWN ─────────────────
    await logger.ainfo("Application shutting down")
    await dispose_db(app)
    await dispose_cm(app)
    await dispose_arq_pool(app)


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A production-grade REST + WebSocket API for a multi-tenant task management platform.",
        lifespan=lifespan,
    )

    init_limiter(app)
    register_exception_handlers(app)
    app.add_middleware(RequestIDMiddleware)
    app.include_router(api_router)

    return app


app = create_app()
