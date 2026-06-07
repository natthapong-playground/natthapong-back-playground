import uuid

import pytest

from app.core.config import settings

pytestmark = pytest.mark.asyncio

REGISTER_URL = f"{settings.API_V1_STR}/users/register"
LOGIN_URL = f"{settings.API_V1_STR}/login"
PROFILE_URL = f"{settings.API_V1_STR}/users/myprofile"
AUDIT_URL = f"{settings.API_V1_STR}/audit-logs"


def _unique_email(prefix: str = "audit") -> str:
    # uuid keeps every test self-contained and independent of run order/timing.
    return f"pytest_{prefix}_{uuid.uuid4().hex}@mail.com"


async def _register(async_client, email: str, password: str, role: str = "Regular"):
    return await async_client.post(
        REGISTER_URL, json={"email": email, "password": password, "role": role}
    )


async def _login(async_client, email: str, password: str) -> str:
    resp = await async_client.post(
        LOGIN_URL, data={"username": email, "password": password}
    )
    return resp.json()["access_token"]


async def _superadmin_token(async_client) -> str:
    email, password = _unique_email("super"), "ValidPassword123"
    await _register(async_client, email, password, role="SuperAdmin")
    return await _login(async_client, email, password)


# --------------------------------------------------------------------------- #
# Access control on GET /audit-logs                                            #
# --------------------------------------------------------------------------- #
async def test_audit_logs_requires_token(async_client):
    response = await async_client.get(AUDIT_URL)
    assert response.status_code == 401


async def test_audit_logs_forbidden_for_regular_user(async_client):
    email, password = _unique_email("regular"), "ValidPassword123"
    await _register(async_client, email, password, role="Regular")
    token = await _login(async_client, email, password)

    response = await async_client.get(
        AUDIT_URL, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


async def test_audit_logs_accessible_for_superadmin(async_client):
    token = await _superadmin_token(async_client)
    response = await async_client.get(
        AUDIT_URL, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# --------------------------------------------------------------------------- #
# Logging policy: mutations and failures are recorded; plain reads are not     #
# --------------------------------------------------------------------------- #
async def test_failed_login_is_logged(async_client):
    # A failed login (401) must be auditable even though no token is involved.
    bad_email = _unique_email("badlogin")
    await async_client.post(
        LOGIN_URL, data={"username": bad_email, "password": "wrongpassword"}
    )

    token = await _superadmin_token(async_client)
    response = await async_client.get(
        AUDIT_URL,
        params={"method": "POST", "status_code": 401, "limit": 200},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    logins = [e for e in response.json() if e["path"] == LOGIN_URL]
    assert logins, "expected the failed POST /login to be recorded"
    assert all(e["actor_user_id"] is None for e in logins)


async def test_register_mutation_is_logged_with_actor_resolution(async_client):
    # Register a SuperAdmin, then have them register a Regular user (a POST that
    # carries a valid token) and confirm the actor is resolved on the entry.
    token = await _superadmin_token(async_client)
    new_email = _unique_email("created")
    create = await async_client.post(
        REGISTER_URL,
        json={"email": new_email, "password": "ValidPassword123", "role": "Regular"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create.status_code == 201

    logs = await async_client.get(
        AUDIT_URL,
        params={"method": "POST", "status_code": 201, "limit": 200},
        headers={"Authorization": f"Bearer {token}"},
    )
    entries = [e for e in logs.json() if e["path"] == REGISTER_URL]
    assert entries, "expected POST /register 201 to be recorded"
    # The most recent matching entry was made by the authenticated SuperAdmin.
    latest = entries[0]
    assert latest["actor_role"] == "SuperAdmin"
    assert latest["actor_user_id"] is not None


async def test_successful_profile_read_is_not_logged(async_client):
    # GET /myprofile success is a non-sensitive read -> must NOT be audited.
    email, password = _unique_email("read"), "ValidPassword123"
    await _register(async_client, email, password, role="Regular")
    token = await _login(async_client, email, password)

    profile = await async_client.get(
        PROFILE_URL, headers={"Authorization": f"Bearer {token}"}
    )
    assert profile.status_code == 200

    admin_token = await _superadmin_token(async_client)
    logs = await async_client.get(
        AUDIT_URL,
        params={"method": "GET", "limit": 200},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    profile_hits = [
        e for e in logs.json()
        if e["path"] == PROFILE_URL and e["status_code"] == 200
    ]
    assert not profile_hits, "successful profile reads should not be logged"
