# src/shared/websocket_auth.py
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User
from src.users.repository import UserRepository
from src.users.tokens import JWTValidationException, decode_token


class WebSocketAuthError(Exception): ...


async def authenticate_websocket(token: str, session: AsyncSession) -> User:
    """Decode the token, validate the type claim and fetch the user.

    Args:
        token: JSON Web Token
        session: database session
    Returns: user model

    Raises:
      WebSocketAuthError: on any failure
    """
    try:
        claims = decode_token(token)
    except JWTValidationException as e:
        raise WebSocketAuthError(e)

    if claims.get("type") != "access" or not (user_id := claims.get("sub")):
        raise WebSocketAuthError("Invalid token")

    try:
        user = await UserRepository(session).get_by_id(uuid.UUID(user_id))
    except ValueError as e:
        raise WebSocketAuthError(e)

    if not user or not user.is_active:
        raise WebSocketAuthError("User not found or inactive")

    return user
