import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from app.schemas.country_schema import ClockSnapshotSchema, CountrySchema
from app.services import timezone_service

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "countries.json"


@lru_cache(maxsize=1)
def _records() -> list[dict]:
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _by_code() -> dict[str, dict]:
    return {r["code"].upper(): r for r in _records()}


def search_countries(*, search: str | None, limit: int) -> list[CountrySchema]:
    now = datetime.now(timezone.utc)
    items = _records()
    if search:
        q = search.casefold()
        items = [r for r in items if q in r["name"].casefold()]
    return [timezone_service.build_country(r, now) for r in items[:limit]]


def get_country(code: str) -> CountrySchema | None:
    record = _by_code().get(code.upper())
    if record is None:
        return None
    return timezone_service.build_country(record, datetime.now(timezone.utc))


def build_snapshot(codes: list[str]) -> ClockSnapshotSchema:
    now = datetime.now(timezone.utc)
    lookup = _by_code()
    countries = [
        timezone_service.build_country(lookup[c], now)
        for c in codes
        if c in lookup
    ]
    return ClockSnapshotSchema(reference_utc=now.isoformat(), countries=countries)
