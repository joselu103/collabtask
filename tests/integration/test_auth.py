# tests/integration/test_auth.py

import faker
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.schemas import (
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from src.users.tokens import create_refresh_token
from tests.factories import UserFactory


async def test_register_user(client: AsyncClient):
    # Given
    fake = faker.Faker()

    user_data = UserCreate(
        email=fake.email(),
        username=fake.user_name(),
        password=fake.password(),
    )

    # When
    response = await client.post(
        url="http://test/api/v1/users/register", json=user_data.model_dump()
    )

    # Then
    assert response.status_code == 201
    UserResponse.model_validate(response.json())


async def test_login(client: AsyncClient, db_session: AsyncSession):
    # Given
    user = UserFactory.build()  # password == email
    db_session.add(user)
    await db_session.commit()

    login_data = {"username": user.email, "password": user.email}

    # When
    response = await client.post(url="http://test/api/v1/users/login", data=login_data)

    # Then
    assert response.status_code == 200
    TokenResponse.model_validate(response.json())
    assert response.json()["access_token"]


async def test_refresh(client: AsyncClient, db_session: AsyncSession):
    # Given
    user = UserFactory.build()  # password == email
    db_session.add(user)
    await db_session.commit()
    refresh_token = create_refresh_token(str(user.id))

    refresh_data = RefreshRequest(refresh_token=refresh_token)

    # When
    response = await client.post(
        url="http://test/api/v1/users/refresh", json=refresh_data.model_dump()
    )

    # Then
    assert response.status_code == 200
    TokenResponse.model_validate(response.json())
    assert response.json()["access_token"]
