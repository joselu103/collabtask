# src/workers/arq_app.py
from arq import create_pool
from arq.connections import RedisSettings
from emails.backend.smtp.aio_backend import AsyncSMTPBackend
from fastapi import FastAPI

from src.database.engine import create_db
from src.settings.settings import get_settings
from src.shared.logging_config import configure_logging
from src.workers.tasks import send_task_assigned_email

settings = get_settings()
REDIS_SETTINGS = RedisSettings.from_dsn(settings.redis_url.get_secret_value())

# Ensure the relationships don't break the worker
from src.organizations.models import Organization, OrganizationMember  # noqa
from src.users.models import User  # noqa


async def startup(ctx) -> None:
    configure_logging()
    engine, factory = create_db()
    ctx["db_engine"] = engine
    ctx["db_session_factory"] = factory
    ctx["smtp_backend"] = AsyncSMTPBackend(
        host=settings.smtp_host,
        port=settings.smtp_port,
        tls=settings.smtp_tls,
        user=settings.smtp_user,
        password=settings.smtp_password.get_secret_value(),
    )


async def shutdown(ctx):
    await ctx["db_engine"].dispose()


class WorkerSettings:
    functions = [send_task_assigned_email]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = REDIS_SETTINGS


async def init_arq_pool(app: FastAPI) -> None:
    pool = await create_pool(REDIS_SETTINGS)
    app.state.arq_pool = pool


async def dispose_arq_pool(app: FastAPI) -> None:
    await app.state.arq_pool.aclose()
