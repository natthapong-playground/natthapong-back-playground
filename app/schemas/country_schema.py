from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class CountrySchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    code: str
    name: str
    timezone: str
    utc_offset_minutes: int
    utc_offset_label: str
    local_time: str
    
class ClockSnapshotSchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    reference_utc: str
    countries: list[CountrySchema]