from sqlalchemy import Column, Integer, String, Boolean
from app.models.base import Base
from datetime import datetime, timezone

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="Regular", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        datetime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        datetime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )