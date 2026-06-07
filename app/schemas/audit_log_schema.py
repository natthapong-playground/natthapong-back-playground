from datetime import datetime
from pydantic import BaseModel

class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    actor_user_id: int | None
    actor_email: str | None
    actor_role: str | None
    method: str
    path: str
    status_code: int
    client_ip: str | None
    user_agent: str | None
    duration_ms: int | None
    request_id: str | None

    class Config:
        from_attributes = True
