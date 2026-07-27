import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token

from app.api.dependencies import get_db, get_redis, oauth2_scheme
from app.services.user_service import (
    authenticate_user,
    GoogleAccountConflictError,
    get_or_create_google_user,
    get_user_by_email,
    InactiveUserError,
)
from app.services.auth_service import revoke_token, is_token_revoked
from app.services import google_auth_service, rate_limit_service
from app.schemas.token_schema import GoogleLoginRequest, Token, RefreshRequest

router = APIRouter()


def _client_ip(request: Request) -> str:
    direct_ip = request.client.host if request.client else "unknown"
    if direct_ip in settings.TRUSTED_PROXY_IPS:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return direct_ip


def _issue_tokens(email: str, role: str) -> dict:
    data = {"sub": email, "role": role}
    return {
        "access_token": create_access_token(data),
        "refresh_token": create_refresh_token(data),
        "token_type": "bearer",
    }


@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    # Brute-force guard: lock the (account + source IP) pair after repeated misses.
    identifier = f"{form_data.username.lower()}|{_client_ip(request)}"
    if await rate_limit_service.is_login_blocked(r, identifier):
        retry_after = await rate_limit_service.get_retry_after(r, identifier)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    try:
        user = await authenticate_user(db, email=form_data.username, password=form_data.password)
    except InactiveUserError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support.",
        )

    if not user:
        await rate_limit_service.record_login_failure(r, identifier)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await rate_limit_service.clear_login_failures(r, identifier)
    return _issue_tokens(user.email, user.role)


@router.post("/google-login", response_model=Token)
async def google_login(
    payload_in: GoogleLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    identifier = _client_ip(request)
    attempt_count = await rate_limit_service.record_google_login_attempt(r, identifier)
    if attempt_count > settings.GOOGLE_LOGIN_RATE_LIMIT_MAX_ATTEMPTS:
        retry_after = await rate_limit_service.get_google_login_retry_after(r, identifier)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many Google sign-in attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    try:
        identity = await google_auth_service.verify_google_credential(payload_in.credential)
    except google_auth_service.GoogleAuthNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured.",
        )
    except google_auth_service.InvalidGoogleCredentialError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate Google credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await get_or_create_google_user(db, identity.email, identity.subject)
    except GoogleAccountConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already registered with another sign-in method.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support.",
        )

    return _issue_tokens(user.email, user.role)


@router.post("/refresh-token", response_model=Token)
async def refresh_access_token(
    payload_in: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(payload_in.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise credentials_exception

    email = payload.get("sub")
    jti = payload.get("jti")
    exp = payload.get("exp")
    if payload.get("type") != "refresh" or email is None or jti is None:
        raise credentials_exception

    if await is_token_revoked(r, jti):
        raise credentials_exception

    user = await get_user_by_email(db, email=email)
    if user is None or not user.is_active:
        raise credentials_exception

    # Rotation: burn the presented refresh token so it cannot be replayed.
    if exp:
        await revoke_token(r, jti, exp)

    return _issue_tokens(user.email, user.role)


async def _revoke_if_valid(r: redis.Redis, raw_token: str, expected_type: str | None = None) -> None:
    try:
        payload = jwt.decode(raw_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return
    if expected_type and payload.get("type") != expected_type:
        return
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp:
        await revoke_token(r, jti, exp)


@router.post("/logout")
async def logout(
    body: RefreshRequest | None = None,
    token: str = Depends(oauth2_scheme),
    r: redis.Redis = Depends(get_redis),
):

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp:
        await revoke_token(r, jti, exp)
    
    if body and body.refresh_token:
        await _revoke_if_valid(r, body.refresh_token, expected_type="refresh")

    return {"message": "Successfully logged out."}
