from sqlalchemy import Column, DateTime, Integer, String
from app.models.base import Base
from datetime import datetime, timezone

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    actor_user_id = Column(Integer, nullable=True, index=True)
    actor_email = Column(String, nullable=True)
    actor_role = Column(String, nullable=True)

    method = Column(String, nullable=False)
    path = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False, index=True)

    client_ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    request_id = Column(String, nullable=True, index=True)
