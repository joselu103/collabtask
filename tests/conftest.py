# tests/conftest.py
from typing import AsyncGenerator

import pytest
from fastapi import Request
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from alembic.command import upgrade
from alembic.config import Config
from src.app import create_app
from src.database.engine import dispose_db, get_db, init_db
from src.settings.settings import get_settings


@pytest.fixture(autouse=True)
async def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True, scope="session")
def upgrade_tables():
    cfg = Config("alembic.ini")
    upgrade(cfg, "head")


async def get_test_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    session = None
    try:
        session_factory = request.app.state.session_factory
        session = session_factory()
        yield session
    finally:
        if session:
            await session.rollback()
            await session.close()


@pytest.fixture
async def app():
    app = create_app()
    init_db(app)
    app.dependency_overrides[get_db] = get_test_db

    yield app

    await dispose_db(app)


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def db_session(app) -> AsyncGenerator[AsyncSession, None]:
    session = None
    try:
        session_factory = app.state.session_factory
        session = session_factory()
        yield session
    finally:
        if session:
            await session.rollback()
            await session.close()
