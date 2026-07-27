import asyncio
import pytest
import time
from uuid import uuid4
from sqlalchemy import delete, select
from app.core.config import settings
from app.core.security import create_access_token
from app.models.base import AsyncSessionLocal
from app.models.user_model import User
from app.services import google_auth_service
pytestmark = pytest.mark.asyncio


async def _register_and_login(async_client) -> str:
    unique_email = f"pytest_{uuid4().hex}@mail.com"
    password = "ThisIsLogoutFlowTesting123"

    payload = {"email": unique_email, "role": "Regular", "password": password}
    await async_client.post(f"{settings.API_V1_STR}/users/register", json=payload)

    login_response = await async_client.post(
        f"{settings.API_V1_STR}/login",
        data={"username": unique_email, "password": password},
    )
    return login_response.json()["access_token"]

async def test_register_new_user(async_client):
    unique_email = f"pytest_{int(time.time())}@mail.com"
    
    payload = {
        "email": unique_email,
        "role": "Regular",
        "password": "ThisIsRegisterNewUserTesting123"
    }
    
    response = await async_client.post(f"{settings.API_V1_STR}/users/register", json=payload)
    
    assert response.status_code == 201
    
    data = response.json()
    
    assert data["email"] == unique_email
    assert "id" in data
    assert "created_at" in data
    assert "hashed_password" not in data  

async def test_get_personal_profile_success(async_client):
    unique_email = f"pytest_{int(time.time())}@mail.com"
    password = "ThisIsRegisterNewUserTesting123"
    
    payload = {
        "email": unique_email,
        "role": "Regular",
        "password": password
    }
    
    await async_client.post(f"{settings.API_V1_STR}/users/register", json=payload)

    login_response = await async_client.post(
        f"{settings.API_V1_STR}/login", 
        data={"username": unique_email, "password": password}
    )

    token = login_response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await async_client.get(f"{settings.API_V1_STR}/users/myprofile", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == unique_email
    assert "hashed_password" not in data

async def test_get_personal_profile_unauthorized(async_client):
    response = await async_client.get(f"{settings.API_V1_STR}/users/myprofile")

    assert response.status_code == 401
    

    assert response.json()["detail"] == "Not authenticated"


async def test_logout_revokes_token(async_client):
    token = await _register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    before = await async_client.get(f"{settings.API_V1_STR}/users/myprofile", headers=headers)
    assert before.status_code == 200

    logout = await async_client.post(f"{settings.API_V1_STR}/logout", headers=headers)
    assert logout.status_code == 200
    assert logout.json()["message"] == "Successfully logged out."

    after = await async_client.get(f"{settings.API_V1_STR}/users/myprofile", headers=headers)
    assert after.status_code == 401


async def test_logout_invalid_token(async_client):
    headers = {"Authorization": "Bearer not-a-real-jwt"}

    response = await async_client.post(f"{settings.API_V1_STR}/logout", headers=headers)

    assert response.status_code == 401


async def test_logout_missing_token(async_client):
    response = await async_client.post(f"{settings.API_V1_STR}/logout")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


async def test_profile_rejects_token_without_sub(async_client):
    # A validly-signed access token that carries no 'sub' must be rejected.
    token = create_access_token({"role": "Regular"})
    response = await async_client.get(
        f"{settings.API_V1_STR}/users/myprofile",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


async def test_profile_rejects_deleted_user(async_client):
    email = f"pytest_{uuid4().hex}@mail.com"
    password = "ThisUserWillBeDeleted123"

    await async_client.post(
        f"{settings.API_V1_STR}/users/register",
        json={"email": email, "role": "Regular", "password": password},
    )
    login = await async_client.post(
        f"{settings.API_V1_STR}/login",
        data={"username": email, "password": password},
    )
    token = login.json()["access_token"]

    # Remove the user while their token is still otherwise valid.
    async with AsyncSessionLocal() as session:
        await session.execute(delete(User).where(User.email == email))
        await session.commit()

    response = await async_client.get(
        f"{settings.API_V1_STR}/users/myprofile",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


async def test_google_login_creates_regular_user(async_client, monkeypatch):
    email = f"pytest_google_{uuid4().hex}@gmail.com"
    verified_email = email
    subject = uuid4().hex

    async def verify(_credential):
        return google_auth_service.GoogleIdentity(email=verified_email, subject=subject)

    monkeypatch.setattr(google_auth_service, "verify_google_credential", verify)
    response = await async_client.post(
        f"{settings.API_V1_STR}/google-login",
        json={"credential": "valid-google-id-token"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalars().one()
    assert user.role == "Regular"
    assert user.hashed_password == f"google:{subject}"

    verified_email = f"changed_{uuid4().hex}@gmail.com"
    repeat = await async_client.post(
        f"{settings.API_V1_STR}/google-login",
        json={"credential": "another-valid-google-id-token"},
    )
    assert repeat.status_code == 200
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.hashed_password == f"google:{subject}")
        )
        assert len(result.scalars().all()) == 1


async def test_google_login_does_not_silently_link_existing_user(async_client, monkeypatch):
    email = f"Pytest_google_existing_{uuid4().hex}@gmail.com"
    password = "ExistingPassword123"
    await async_client.post(
        f"{settings.API_V1_STR}/users/register",
        json={"email": email, "role": "Regular", "password": password},
    )

    async def verify(_credential):
        return google_auth_service.GoogleIdentity(email=email.lower(), subject=uuid4().hex)

    monkeypatch.setattr(google_auth_service, "verify_google_credential", verify)
    response = await async_client.post(
        f"{settings.API_V1_STR}/google-login",
        json={"credential": "valid-google-id-token"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "This email is already registered with another sign-in method."
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        assert len(result.scalars().all()) == 1


async def test_google_login_rejects_invalid_credential(async_client, monkeypatch):
    async def reject(_credential):
        raise google_auth_service.InvalidGoogleCredentialError()

    monkeypatch.setattr(google_auth_service, "verify_google_credential", reject)
    response = await async_client.post(
        f"{settings.API_V1_STR}/google-login",
        json={"credential": "invalid-google-id-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate Google credentials."


async def test_google_login_is_rate_limited_before_verification(async_client, monkeypatch):
    calls = 0

    async def reject(_credential):
        nonlocal calls
        calls += 1
        raise google_auth_service.InvalidGoogleCredentialError()

    monkeypatch.setattr(settings, "GOOGLE_LOGIN_RATE_LIMIT_MAX_ATTEMPTS", 1)
    monkeypatch.setattr(google_auth_service, "verify_google_credential", reject)

    responses = await asyncio.gather(
        *(
            async_client.post(
                f"{settings.API_V1_STR}/google-login",
                json={"credential": f"invalid-google-id-token-{index}"},
            )
            for index in range(4)
        )
    )

    assert sorted(response.status_code for response in responses) == [401, 429, 429, 429]
    assert calls == 1


async def test_google_login_rejects_inactive_user(async_client, monkeypatch):
    email = f"pytest_google_inactive_{uuid4().hex}@gmail.com"
    subject = uuid4().hex
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                email=email,
                hashed_password=f"google:{subject}",
                role="Regular",
                is_active=False,
            )
        )
        await session.commit()

    async def verify(_credential):
        return google_auth_service.GoogleIdentity(email=email, subject=subject)

    monkeypatch.setattr(google_auth_service, "verify_google_credential", verify)
    response = await async_client.post(
        f"{settings.API_V1_STR}/google-login",
        json={"credential": "valid-google-id-token"},
    )

    assert response.status_code == 403


async def test_verify_google_credential_returns_verified_email(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(
        google_auth_service.id_token,
        "verify_oauth2_token",
        lambda credential, request, audience: {
            "email": "Verified.User@Gmail.com",
            "email_verified": True,
            "sub": "google-subject-123",
        },
    )

    email = await google_auth_service.verify_google_credential("valid-token")

    assert email.email == "verified.user@gmail.com"
    assert email.subject == "google-subject-123"


async def test_verify_google_credential_requires_verified_email(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(
        google_auth_service.id_token,
        "verify_oauth2_token",
        lambda credential, request, audience: {
            "email": "unverified@gmail.com",
            "email_verified": False,
            "sub": "google-subject-456",
        },
    )

    with pytest.raises(google_auth_service.InvalidGoogleCredentialError):
        await google_auth_service.verify_google_credential("unverified-token")
