import pytest

pytestmark = pytest.mark.asyncio


async def test_health_reports_ok(async_client):
    # With Postgres + Redis up, /health returns 200 and both deps healthy.
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["database"] is True
    assert body["redis"] is True
