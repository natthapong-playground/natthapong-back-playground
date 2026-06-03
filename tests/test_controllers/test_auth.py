import pytest
import time
from uuid import uuid4
from app.core.config import settings
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