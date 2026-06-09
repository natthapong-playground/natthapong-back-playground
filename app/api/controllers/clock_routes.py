from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user
from app.schemas.country_schema import ClockSnapshotSchema
from app.services import country_service

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/clock", response_model=ClockSnapshotSchema)
async def clock_snapshot(code: str = Query(...)):
    code_list = [c.strip().upper() for c in code.split(",") if c.strip()]
    return country_service.build_snapshot(code_list)