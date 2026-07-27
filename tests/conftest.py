import uuid

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.models.base import engine, Base
from app.models import user_model

@pytest.fixture
async def async_client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Unique source IP per test so per-IP / per-account rate-limit counters in the
    # shared Redis never bleed across tests (or across runs).
    h = uuid.uuid4().int
    fake_ip = f"{10 + h % 200}.{(h >> 8) % 256}.{(h >> 16) % 256}.{(h >> 24) % 256}"
    transport = ASGITransport(app=app, client=(fake_ip, 123))
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture
async def auth_headers(async_client):
    """Authorization header for a freshly-registered, logged-in Regular user.

    Use on any endpoint that only needs a valid token (no specific role), e.g.
    the country/clock routes. The unique email keeps each test self-contained.
    """
    email = f"pytest_auth_{uuid.uuid4().hex}@mail.com"
    password = "ValidPassword123"
    await async_client.post(
        f"{settings.API_V1_STR}/users/register",
        json={"email": email, "password": password, "role": "Regular"},
    )
    resp = await async_client.post(
        f"{settings.API_V1_STR}/login",
        data={"username": email, "password": password},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
