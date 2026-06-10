import uuid

import pytest

from app.core.config import settings

pytestmark = pytest.mark.asyncio

REGISTER_URL = f"{settings.API_V1_STR}/users/register"
LOGIN_URL = f"{settings.API_V1_STR}/login"

MAX_ATTEMPTS = settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS


def _unique_email() -> str:
    # Unique email keeps each test's rate-limit counter isolated in shared Redis.
    return f"pytest_ratelimit_{uuid.uuid4().hex}@mail.com"


async def _register(async_client, email: str, password: str = "ValidPassword123"):
    await async_client.post(
        REGISTER_URL, json={"email": email, "password": password, "role": "Regular"}
    )


async def test_login_locks_out_after_max_failures(async_client):
    email = _unique_email()
    await _register(async_client, email)

    # The first MAX_ATTEMPTS failures are answered with 401.
    for _ in range(MAX_ATTEMPTS):
        resp = await async_client.post(
            LOGIN_URL, data={"username": email, "password": "WrongPassword999"}
        )
        assert resp.status_code == 401

    # The next attempt is locked out, even with the *correct* password.
    blocked = await async_client.post(
        LOGIN_URL, data={"username": email, "password": "WrongPassword999"}
    )
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers

    correct = await async_client.post(
        LOGIN_URL, data={"username": email, "password": "ValidPassword123"}
    )
    assert correct.status_code == 429


async def test_successful_login_resets_failure_counter(async_client):
    email = _unique_email()
    password = "ValidPassword123"
    await _register(async_client, email, password)

    # A few failures, but below the threshold.
    for _ in range(MAX_ATTEMPTS - 1):
        resp = await async_client.post(
            LOGIN_URL, data={"username": email, "password": "WrongPassword999"}
        )
        assert resp.status_code == 401

    # A success clears the counter...
    ok = await async_client.post(LOGIN_URL, data={"username": email, "password": password})
    assert ok.status_code == 200

    # ...so the next wrong password is a plain 401, not a lockout.
    after = await async_client.post(
        LOGIN_URL, data={"username": email, "password": "WrongPassword999"}
    )
    assert after.status_code == 401
