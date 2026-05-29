# src/users/tokens.py
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from src.settings.settings import get_settings


class JWTValidationException(Exception): ...


def create_access_token(subject: str) -> str:
    """Generate an access token with HS256 encoding.

    The secret key and expire time are set from the global settings.

    Args:
        subject: user identifier to insert as "sub" claim.

    Returns:
        Access JSON Web Token in string format.
    """
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    return jwt.encode(
        payload={"sub": subject, "exp": expires_at, "type": "access"},
        key=settings.secret_key.get_secret_value(),
        algorithm="HS256",
    )


def create_refresh_token(subject: str) -> str:
    """Generate a refresh token with HS256 encoding.

    The secret key and expire time are set from the global settings.

    Args:
        subject: user identifier to insert as "sub" claim.

    Returns:
        Refresh JSON Web Token in string format.
    """
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )

    return jwt.encode(
        payload={"sub": subject, "exp": expires_at, "type": "refresh"},
        key=settings.secret_key.get_secret_value(),
        algorithm="HS256",
    )


def decode_token(token: str) -> dict[str, Any]:
    """Verify a JSON Web Token encoded using HS256 and return its claims.

    Args:
        token: JWT in string format.

    Returns:
        Dictionary with token claims.

    Raises:
        JWTValidationException: If the token is invalid, expired or the
            secret key is incorrect.
    """
    settings = get_settings()
    try:
        return jwt.decode(
            token, key=settings.secret_key.get_secret_value(), algorithms=("HS256",)
        )
    except (
        jwt.exceptions.ExpiredSignatureError,
        jwt.exceptions.InvalidSignatureError,
        jwt.DecodeError,
    ) as e:
        raise JWTValidationException(e)
