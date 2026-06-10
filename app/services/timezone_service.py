from datetime import datetime
from zoneinfo import ZoneInfo

from app.schemas.country_schema import CountrySchema

def build_country(record: dict, reference_utc: datetime) -> CountrySchema:
    tz = ZoneInfo(record["timezone"])
    local = reference_utc.astimezone(tz)
    offset_min = int(local.utcoffset().total_seconds() // 60)
    sign = "+" if offset_min >= 0 else "-"
    hh, mm = divmod(abs(offset_min), 60)
    return CountrySchema(
        code=record["code"],
        name=record["name"],
        timezone=record["timezone"],
        utc_offset_minutes=offset_min,
        utc_offset_label=f"UTC{sign}{hh:02d}:{mm:02d}",
        local_time=local.isoformat(),
    )
