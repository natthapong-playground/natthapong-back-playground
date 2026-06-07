import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.base import engine, Base
from app.models import user_model  

@pytest.fixture
async def async_client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client