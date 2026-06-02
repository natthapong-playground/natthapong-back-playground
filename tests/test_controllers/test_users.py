import uuid

import pytest
from sqlalchemy import update

from app.core.config import settings
from app.models.base import AsyncSessionLocal
from app.models.user_model import User

pytestmark = pytest.mark.asyncio

REGISTER_URL = f"{settings.API_V1_STR}/users/register"
LOGIN_URL = f"{settings.API_V1_STR}/login"
PROFILE_URL = f"{settings.API_V1_STR}/users/myprofile"


def _unique_email() -> str:
    # uuid keeps every test self-contained and independent of run order/timing.
    return f"pytest_users_{uuid.uuid4().hex}@mail.com"


async def _register(async_client, payload: dict):
    return await async_client.post(REGISTER_URL, json=payload)


# --------------------------------------------------------------------------- #
# POST /users/register                                                         #
# --------------------------------------------------------------------------- #
async def test_register_duplicate_email(async_client):
    payload = {
        "email": _unique_email(),
        "password": "ValidPassword123",
        "role": "Regular",
    }

    first = await _register(async_client, payload)
    assert first.status_code == 201

    second = await _register(async_client, payload)
    assert second.status_code == 400
    assert second.json()["detail"] == "Email is already registered"


async def test_register_password_too_short(async_client):
    payload = {
        "email": _unique_email(),
        "password": "short",  # < 8 chars -> schema validation error
        "role": "Regular",
    }
    response = await _register(async_client, payload)
    assert response.status_code == 422


async def test_register_invalid_email(async_client):
    payload = {
        "email": "not-an-email",
        "password": "ValidPassword123",
        "role": "Regular",
    }
    response = await _register(async_client, payload)
    assert response.status_code == 422


async def test_register_invalid_role(async_client):
    payload = {
        "email": _unique_email(),
        "password": "ValidPassword123",
        "role": "King",  # outside the allowed RoleType literal
    }
    response = await _register(async_client, payload)
    assert response.status_code == 422


async def test_register_missing_password(async_client):
    payload = {"email": _unique_email(), "role": "Regular"}
    response = await _register(async_client, payload)
    assert response.status_code == 422


async def test_register_defaults_role_to_regular(async_client):
    # role omitted -> UserBase default of "Regular".
    payload = {"email": _unique_email(), "password": "ValidPassword123"}
    response = await _register(async_client, payload)
    assert response.status_code == 201
    assert response.json()["role"] == "Regular"


# --------------------------------------------------------------------------- #
# GET /users/myprofile  (token edge cases not covered by test_auth.py)         #
# --------------------------------------------------------------------------- #
async def test_profile_malformed_token(async_client):
    headers = {"Authorization": "Bearer this.is.not.a.valid.jwt"}
    response = await async_client.get(PROFILE_URL, headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


async def test_profile_inactive_user(async_client):
    # Obtain a genuinely valid token, then deactivate the user behind its back.
    email = _unique_email()
    password = "ValidPassword123"
    await _register(
        async_client,
        {"email": email, "password": password, "role": "Regular"},
    )

    login = await async_client.post(
        LOGIN_URL, data={"username": email, "password": password}
    )
    token = login.json()["access_token"]

    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User).where(User.email == email).values(is_active=False)
        )
        await session.commit()

    response = await async_client.get(
        PROFILE_URL, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
