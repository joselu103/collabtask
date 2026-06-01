# src/users/router.py

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.engine import get_db, transaction
from src.shared.limiter import limiter
from src.users.schemas import (
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from src.users.service import LoginError, RefreshError, RegisterError, UserService

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
    request: Request,  # Necessary for limiter
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


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login_user(
    user_service: Annotated[UserService, Depends(get_user_service)],
    user_data: UserLogin,
    request: Request,  # Necessary for limiter
) -> TokenResponse:
    """Login user with email and password.

    Returns:
        Access and Refresh tokens.

    Raises:
        HTTPException(401): Wrong email or password.
    """
    try:
        access_token, refresh_token = await user_service.login(user_data)
        return TokenResponse(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )
    except LoginError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email or password.")


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_user(
    user_service: Annotated[UserService, Depends(get_user_service)],
    refresh_data: RefreshRequest,
    request: Request,  # Necessary for limiter
) -> TokenResponse:
    """Attempt to obtain a new access token with a refresh token.

    Returns:
        Access and Refresh tokens.

    Raises:
        HTTPException(401): Refresh token expired or revoked.
    """
    try:
        access_token, refresh_token = await user_service.refresh(refresh_data)
        return TokenResponse(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )
    except RefreshError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email or password.")
