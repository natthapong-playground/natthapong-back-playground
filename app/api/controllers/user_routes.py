import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_model import User
from app.schemas.user_schema import UserCreate, UserResponse
from app.services import user_service, rate_limit_service
from app.api.dependencies import get_current_user, get_db, get_redis

router = APIRouter()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# CREATE
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    # Multiple signups per source IP to stop registration spam.
    identifier = _client_ip(request)
    if await rate_limit_service.is_register_blocked(r, identifier):
        retry_after = await rate_limit_service.get_register_retry_after(r, identifier)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    await rate_limit_service.record_register_attempt(r, identifier)

    existing_user = await user_service.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )
    new_user = await user_service.create_user(db=db, user_in=user_in)
    return new_user

@router.get("/myprofile", response_model=UserResponse)
async def read_users_own_profile(current_user: User = Depends(get_current_user)):
    return current_user