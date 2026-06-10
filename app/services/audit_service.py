from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.audit_log_model import AuditLog

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

SENSITIVE_GET_PREFIXES = (
    f"{settings.API_V1_STR}/audit-logs",
)


def should_log(method: str, path: str, status_code: int) -> bool:
    if method in MUTATING_METHODS:
        return True
    if status_code >= 400:            # every failure, include GET 401/403/422
        return True
    if method == "GET" and path.startswith(SENSITIVE_GET_PREFIXES):
        return True
    return False


async def create_log(
    db: AsyncSession,
    *,
    method: str,
    path: str,
    status_code: int,
    actor_user_id: int | None = None,
    actor_email: str | None = None,
    actor_role: str | None = None,
    client_ip: str | None = None,
    user_agent: str | None = None,
    duration_ms: int | None = None,
    request_id: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        method=method,
        path=path,
        status_code=status_code,
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        actor_role=actor_role,
        client_ip=client_ip,
        user_agent=user_agent,
        duration_ms=duration_ms,
        request_id=request_id,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def query_logs(
    db: AsyncSession,
    *,
    actor_user_id: int | None = None,
    method: str | None = None,
    status_code: int | None = None,
    skip: int = 0,
    limit: int = 150,
) -> list[AuditLog]:
    stmt = select(AuditLog)
    if actor_user_id is not None:
        stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
    if method is not None:
        stmt = stmt.where(AuditLog.method == method.upper())
    if status_code is not None:
        stmt = stmt.where(AuditLog.status_code == status_code)
    stmt = stmt.order_by(AuditLog.id.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
