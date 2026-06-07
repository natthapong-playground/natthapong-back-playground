import uuid

import pytest
from sqlalchemy import update

from app.core.config import settings
from app.models.base import AsyncSessionLocal
from app.models.user_model import User

pytestmark = pytest.mark.asyncio

REGISTER_URL = f"{settings.API_V1_STR}/users/register"
LOGIN_URL = f"{settings.API_V1_STR}/login"


def _unique_email() -> str:
    # uuid keeps every test self-contained and independent of run order/timing.
    return f"pytest_login_{uuid.uuid4().hex}@mail.com"


async def _register(async_client, email: str, password: str, role: str = "Regular"):
    return await async_client.post(
        REGISTER_URL,
        json={"email": email, "password": password, "role": role},
    )


async def test_login_success(async_client):
    email = _unique_email()
    password = "ValidPassword123"
    await _register(async_client, email, password)

    response = await async_client.post(
        LOGIN_URL, data={"username": email, "password": password}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data
    assert data["access_token"]


async def test_login_wrong_password(async_client):
    email = _unique_email()
    await _register(async_client, email, "ValidPassword123")

    response = await async_client.post(
        LOGIN_URL, data={"username": email, "password": "WrongPassword999"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password."


async def test_login_nonexistent_email(async_client):
    response = await async_client.post(
        LOGIN_URL,
        data={"username": _unique_email(), "password": "ValidPassword123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password."


async def test_login_inactive_user(async_client):
    email = _unique_email()
    password = "ValidPassword123"
    await _register(async_client, email, password)

    # Deactivate the freshly-created user so authenticate_user raises InactiveUserError.
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User).where(User.email == email).values(is_active=False)
        )
        await session.commit()

    response = await async_client.post(
        LOGIN_URL, data={"username": email, "password": password}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Your account has been deactivated. Please contact support."
    )
