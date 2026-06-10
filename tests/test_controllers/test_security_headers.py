import pytest

from app.core.config import settings

pytestmark = pytest.mark.asyncio

PROFILE_URL = f"{settings.API_V1_STR}/users/myprofile"


async def test_security_headers_present_on_success(async_client):
    # Also covers the root endpoint (no auth, not audited).
    resp = await async_client.get("/")
    assert resp.status_code == 200
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in resp.headers["Content-Security-Policy"]
    assert "max-age=63072000" in resp.headers["Strict-Transport-Security"]
    assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in resp.headers["Permissions-Policy"]


async def test_security_headers_present_on_error(async_client):
    # Hardening headers must ride on error responses too (here an unauth 401).
    resp = await async_client.get(PROFILE_URL)
    assert resp.status_code == 401
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert "Strict-Transport-Security" in resp.headers
