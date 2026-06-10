import uuid
from datetime import timedelta

import pytest
from sqlalchemy import update

from app.core.config import settings
from app.core.security import create_access_token
from app.models.base import AsyncSessionLocal
from app.models.user_model import User

pytestmark = pytest.mark.asyncio

REGISTER_URL = f"{settings.API_V1_STR}/users/register"
LOGIN_URL = f"{settings.API_V1_STR}/login"
REFRESH_URL = f"{settings.API_V1_STR}/refresh-token"
LOGOUT_URL = f"{settings.API_V1_STR}/logout"
PROFILE_URL = f"{settings.API_V1_STR}/users/myprofile"


def _unique_email() -> str:
    return f"pytest_refresh_{uuid.uuid4().hex}@mail.com"


async def _register_and_login(async_client) -> dict:
    email = _unique_email()
    password = "ValidPassword123"
    await async_client.post(
        REGISTER_URL, json={"email": email, "password": password, "role": "Regular"}
    )
    resp = await async_client.post(LOGIN_URL, data={"username": email, "password": password})
    return resp.json()


async def test_login_returns_refresh_token(async_client):
    data = await _register_and_login(async_client)

    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["access_token"] != data["refresh_token"]


async def test_refresh_returns_usable_access_token(async_client):
    tokens = await _register_and_login(async_client)

    resp = await async_client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]

    # The freshly minted access token works on a protected route.
    profile = await async_client.get(
        PROFILE_URL, headers={"Authorization": f"Bearer {new_tokens['access_token']}"}
    )
    assert profile.status_code == 200


async def test_refresh_rotates_and_revokes_old_token(async_client):
    tokens = await _register_and_login(async_client)
    refresh = tokens["refresh_token"]

    first = await async_client.post(REFRESH_URL, json={"refresh_token": refresh})
    assert first.status_code == 200

    # Replaying the same refresh token is rejected (it was rotated/revoked).
    second = await async_client.post(REFRESH_URL, json={"refresh_token": refresh})
    assert second.status_code == 401


async def test_refresh_rejects_access_token(async_client):
    tokens = await _register_and_login(async_client)

    resp = await async_client.post(REFRESH_URL, json={"refresh_token": tokens["access_token"]})
    assert resp.status_code == 401


async def test_refresh_rejects_garbage_token(async_client):
    resp = await async_client.post(REFRESH_URL, json={"refresh_token": "not-a-real-jwt"})
    assert resp.status_code == 401


async def test_refresh_missing_body_is_422(async_client):
    resp = await async_client.post(REFRESH_URL)
    assert resp.status_code == 422


async def test_refresh_rejected_for_inactive_user(async_client):
    email = _unique_email()
    password = "ValidPassword123"
    await async_client.post(
        REGISTER_URL, json={"email": email, "password": password, "role": "Regular"}
    )
    login = await async_client.post(LOGIN_URL, data={"username": email, "password": password})
    refresh_token = login.json()["refresh_token"]

    # Deactivate the account after the refresh token was issued.
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User).where(User.email == email).values(is_active=False)
        )
        await session.commit()

    # A valid-but-now-inactive user's refresh token must be rejected.
    resp = await async_client.post(REFRESH_URL, json={"refresh_token": refresh_token})
    assert resp.status_code == 401


async def test_access_route_rejects_refresh_token(async_client):
    tokens = await _register_and_login(async_client)

    # A refresh token must not authenticate on protected routes.
    resp = await async_client.get(
        PROFILE_URL, headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
    )
    assert resp.status_code == 401


async def test_logout_revokes_refresh_token(async_client):
    tokens = await _register_and_login(async_client)

    logout = await async_client.post(
        LOGOUT_URL,
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout.status_code == 200

    # After logout the refresh token is dead — it can no longer mint new tokens.
    resp = await async_client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401


async def test_logout_with_expired_access_still_revokes_refresh(async_client):
    email = _unique_email()
    password = "ValidPassword123"
    await async_client.post(
        REGISTER_URL, json={"email": email, "password": password, "role": "Regular"}
    )
    login = await async_client.post(LOGIN_URL, data={"username": email, "password": password})
    refresh_token = login.json()["refresh_token"]

    # Simulate logging out after the 60-min access token has already lapsed.
    expired_access = create_access_token(
        {"sub": email, "role": "Regular"}, expires_delta=timedelta(seconds=-1)
    )

    logout = await async_client.post(
        LOGOUT_URL,
        headers={"Authorization": f"Bearer {expired_access}"},
        json={"refresh_token": refresh_token},
    )
    assert logout.status_code == 200

    # The refresh token must still be revoked despite the expired access token.
    resp = await async_client.post(REFRESH_URL, json={"refresh_token": refresh_token})
    assert resp.status_code == 401
