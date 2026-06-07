import time

from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.models.base import AsyncSessionLocal
from app.services import audit_service, user_service


def _extract_actor(request) -> tuple[str | None, str | None]:
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        return None, None
    token = auth[7:].strip()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub"), payload.get("role")
    except JWTError:
        return None, None


def _client_ip(request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)

        method = request.method
        path = request.url.path
        status_code = response.status_code

        if not audit_service.should_log(method, path, status_code):
            return response

        # Logging must never break the actual request.
        try:
            actor_email, actor_role = _extract_actor(request)
            actor_user_id = None
            async with AsyncSessionLocal() as session:
                if actor_email:
                    user = await user_service.get_user_by_email(session, email=actor_email)
                    if user:
                        actor_user_id = user.id
                await audit_service.create_log(
                    session,
                    method=method,
                    path=path,
                    status_code=status_code,
                    actor_user_id=actor_user_id,
                    actor_email=actor_email,
                    actor_role=actor_role,
                    client_ip=_client_ip(request),
                    user_agent=request.headers.get("User-Agent"),
                    duration_ms=duration_ms,
                    request_id=request.headers.get("X-Request-ID"),
                )
        except Exception:
            pass

        return response
