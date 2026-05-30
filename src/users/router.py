# src/users/router.py

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.engine import get_db, transaction
from src.shared.limiter import limiter
from src.users.schemas import UserCreate, UserResponse
from src.users.service import RegisterError, UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserService:
    return UserService(session)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("10/minute")
async def register_user(
    user_service: Annotated[UserService, Depends(get_user_service)],
    user_data: UserCreate,
    request: Request,
) -> UserResponse:
    """Create new user with email, username and password.

    Returns:
        New user data.

    Raises:
        HTTPException(409): Username or email already in use.
    """
    try:
        async with transaction(user_service.session):
            new_user = await user_service.register_new_user(user_data)
            return UserResponse.model_validate(new_user)
    except RegisterError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Username or email already in use."
        )
