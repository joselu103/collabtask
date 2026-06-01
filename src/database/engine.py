from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.settings.settings import get_settings


def create_db() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Initialize the async database engine and session factory.

    Reads database configuration from settings and attaches the engine
    and session factory to app.state for use across the application.

    Returns:
        Tuple containing the async database engine and the session
        factory.
    """
    settings = get_settings()

    async_engine = create_async_engine(
        url=settings.database_url.get_secret_value(), echo=False
    )
    session_factory = async_sessionmaker(
        bind=async_engine, expire_on_commit=False, class_=AsyncSession
    )
    return async_engine, session_factory


def init_db(app: FastAPI) -> None:
    """Calls create_db and store the async database engine and session
    factory in app.state.

    Args:
        app: The FastAPI application instance.Must have settings with a
            valid database_url configured.
    """
    async_engine, session_factory = create_db()

    app.state.engine = async_engine
    app.state.session_factory = session_factory


async def dispose_db(app: FastAPI) -> None:
    """Dispose the async database engine.

    Obtains the engine from app.state.

    Args:
        app: The FastAPI application instance. Must contain the engine
            in its state attribute.
    """
    await app.state.engine.dispose()


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Generate async database session.

    Args:
        request: HTTP request
    """
    try:
        session_factory = request.app.state.session_factory
        session = session_factory()
        yield session
    finally:
        await session.close()


@asynccontextmanager
async def transaction(session: AsyncSession):
    """Transaction context to be used in services to handle
    commit/rollback depending on the result.
    """
    try:
        yield
        await session.commit()
    except Exception:
        await session.rollback()
        raise
