import pytest
import time
from app.core.config import settings
pytestmark = pytest.mark.asyncio

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
    
    await async_client.post(f"{settings.API_V1_STR}/users/", json=payload)

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