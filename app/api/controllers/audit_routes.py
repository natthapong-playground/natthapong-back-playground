from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_roles
from app.models.user_model import User
from app.schemas.audit_log_schema import AuditLogResponse
from app.services import audit_service

router = APIRouter()


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    actor_user_id: int | None = Query(None),
    method: str | None = Query(None),
    status_code: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(150, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("SuperAdmin")),
):
    return await audit_service.query_logs(
        db,
        actor_user_id=actor_user_id,
        method=method,
        status_code=status_code,
        skip=skip,
        limit=limit,
    )
