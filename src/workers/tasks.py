# src/workers/tasks.py
import uuid

import structlog
from emails.backend.smtp.aio_backend import AsyncSMTPBackend
from emails.message import Message

from src.settings.settings import get_settings
from src.users.repository import UserRepository

logger = structlog.get_logger()
settings = get_settings()


class UserNotFound(Exception): ...


async def send_task_assigned_email(ctx: dict, user_id: str, task_title: str) -> None:
    """Send an email to an user when is assigneed a task

    Args:
        ctx: arq context dictionary.
        user_id: uuid of the user.
        task_title: title of the asigned task.

    Raises:
        UserNotFound: when no user has that id.
    """
    await logger.adebug("Sending task assign notification")
    async with ctx["db_session_factory"]() as session:
        user = await UserRepository(session).get_by_id(uuid.UUID(user_id))
        if not user:
            raise UserNotFound(user_id)

    message = Message(
        subject="You have been assigned a new task", text=f"Task: '{task_title}'"
    )
    try:
        backend: AsyncSMTPBackend = ctx["smtp_backend"]
        async with backend:
            await backend.sendmail(
                from_addr=settings.email_from,
                to_addrs=user.email,
                msg=message,
            )
    except Exception:
        await logger.aexception("Error while sending email notification")
