from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4
from jose import jwt
import bcrypt
from app.core.config import settings


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash_bytes)

def _create_token(data: dict, token_type: str, default_minutes: int, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=default_minutes)

    to_encode.update({"exp": expire, "jti": str(uuid4()), "type": token_type})

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    return _create_token(data, "access", settings.ACCESS_TOKEN_EXPIRE_MINUTES, expires_delta)

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    return _create_token(data, "refresh", settings.REFRESH_TOKEN_EXPIRE_MINUTES, expires_delta)