# src/users/security.py
from functools import lru_cache

from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher


@lru_cache
def _get_hasher() -> PasswordHash:
    return PasswordHash((BcryptHasher(),))


def hash_password(plain: str) -> str:
    """Hash a plain-text password using bcrypt.

    The resulting hash includes a randomly generated salt and is
    safe to store directly in the database.
    """
    return _get_hasher().hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.

    Returns True if the password matches, False otherwise.
    """
    return _get_hasher().verify(plain, hashed)
