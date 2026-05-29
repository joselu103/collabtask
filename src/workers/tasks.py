# src/workers/tasks.py
import uuid

from emails.backend.smtp.aio_backend import AsyncSMTPBackend
from emails.message import Message

from src.settings.settings import get_settings
from src.users.repository import UserRepository

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
    async with ctx["db_session_factory"]() as session:
        user = await UserRepository(session).get_by_id(uuid.UUID(user_id))
        if not user:
            raise UserNotFound(user_id)

    message = Message(
        subject="You have been assigned a new task", message=f"Task: '{task_title}'"
    )
    backend: AsyncSMTPBackend = ctx["smtp_backend"]
    async with backend:
        await backend.sendmail(
            from_addr=settings.email_from,
            to_addrs=user.email,
            msg=message,
        )
