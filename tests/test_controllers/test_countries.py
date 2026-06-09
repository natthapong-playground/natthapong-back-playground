import pytest

from app.core.config import settings

pytestmark = pytest.mark.asyncio

COUNTRIES_URL = f"{settings.API_V1_STR}/countries"


# --------------------------------------------------------------------------- #
# Auth: any logged-in user may read; anonymous callers are rejected            #
# --------------------------------------------------------------------------- #
async def test_search_requires_token(async_client):
    response = await async_client.get(COUNTRIES_URL)
    assert response.status_code == 401


async def test_get_one_requires_token(async_client):
    response = await async_client.get(f"{COUNTRIES_URL}/JP")
    assert response.status_code == 401


# --------------------------------------------------------------------------- #
# GET /countries (search)                                                      #
# --------------------------------------------------------------------------- #
async def test_search_returns_camelcase_records(async_client, auth_headers):
    response = await async_client.get(
        COUNTRIES_URL, params={"limit": 5}, headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list) and len(body) <= 5
    first = body[0]
    # Pydantic alias_generator=to_camel -> JSON keys are camelCase.
    assert set(first) >= {
        "code", "name", "timezone",
        "utcOffsetMinutes", "utcOffsetLabel", "localTime", "flagEmoji",
    }
    assert first["utcOffsetLabel"].startswith("UTC")


async def test_search_filters_by_name(async_client, auth_headers):
    response = await async_client.get(
        COUNTRIES_URL, params={"search": "scot"}, headers=auth_headers
    )
    assert response.status_code == 200
    names = {c["name"] for c in response.json()}
    assert "Scotland" in names


async def test_search_respects_limit(async_client, auth_headers):
    response = await async_client.get(
        COUNTRIES_URL, params={"limit": 3}, headers=auth_headers
    )
    assert response.status_code == 200
    assert len(response.json()) == 3


async def test_search_limit_out_of_range_is_422(async_client, auth_headers):
    response = await async_client.get(
        COUNTRIES_URL, params={"limit": 999}, headers=auth_headers
    )
    assert response.status_code == 422


# --------------------------------------------------------------------------- #
# GET /countries/{code}                                                        #
# --------------------------------------------------------------------------- #
async def test_get_country_is_case_insensitive(async_client, auth_headers):
    response = await async_client.get(f"{COUNTRIES_URL}/jp", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "JP"
    assert body["name"] == "Japan"
    assert body["timezone"] == "Asia/Tokyo"


async def test_get_country_unknown_code_is_404(async_client, auth_headers):
    response = await async_client.get(f"{COUNTRIES_URL}/ZZ", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown country code"
