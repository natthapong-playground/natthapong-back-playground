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
    
    response = await async_client.post(f"{settings.API_V1_STR}/users/", json=payload)
    
    assert response.status_code == 201
    
    data = response.json()
    
    assert data["email"] == unique_email
    assert "id" in data
    assert "created_at" in data
    assert "hashed_password" not in data  