import pytest

from app.core.config import settings

pytestmark = pytest.mark.asyncio

CLOCK_URL = f"{settings.API_V1_STR}/clock"


# --------------------------------------------------------------------------- #
# Auth                                                                         #
# --------------------------------------------------------------------------- #
async def test_clock_requires_token(async_client):
    response = await async_client.get(CLOCK_URL, params={"code": "TH"})
    assert response.status_code == 401


# --------------------------------------------------------------------------- #
# GET /clock (batch snapshot)                                                  #
# --------------------------------------------------------------------------- #
async def test_clock_returns_shared_reference_and_preserves_order(
    async_client, auth_headers
):
    response = await async_client.get(
        CLOCK_URL, params={"code": "TH,JP,GB-SCT"}, headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert "referenceUtc" in body
    assert [c["code"] for c in body["countries"]] == ["TH", "JP", "GB-SCT"]


async def test_clock_skips_unknown_codes(async_client, auth_headers):
    response = await async_client.get(
        CLOCK_URL, params={"code": "TH,ZZ,JP"}, headers=auth_headers
    )
    assert response.status_code == 200
    codes = [c["code"] for c in response.json()["countries"]]
    assert codes == ["TH", "JP"]  # unknown ZZ dropped, order kept


async def test_clock_missing_code_param_is_422(async_client, auth_headers):
    # Auth passes (header present); validation then rejects the missing query.
    response = await async_client.get(CLOCK_URL, headers=auth_headers)
    assert response.status_code == 422
