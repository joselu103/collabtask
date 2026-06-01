# tests/unit/test_user_service.py
from unittest.mock import AsyncMock

import faker
import pytest
import structlog

from src.users.schemas import UserCreate
from src.users.security import verify_password
from src.users.service import UserService

logger = structlog.get_logger()


@pytest.fixture
def user_service():
    service = UserService(session=AsyncMock())
    service.user_repo = AsyncMock()
    return service


async def test_register_new_user(user_service):
    # Given
    fake = faker.Faker()
    user_data = UserCreate(
        email=fake.email(), username=fake.user_name(), password=fake.password()
    )

    # When
    await user_service.register_new_user(user_data)

    # Then
    repo = user_service.user_repo
    repo.create.assert_called_once()
    user = repo.create.call_args.args[0]

    assert verify_password(user_data.password, user.hashed_password)
