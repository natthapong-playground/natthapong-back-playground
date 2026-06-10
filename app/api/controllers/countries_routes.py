from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_current_user
from app.schemas.country_schema import CountrySchema
from app.services import country_service

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/countries", response_model=list[CountrySchema])
async def search_countries(
    search: str | None = Query(None),
    limit: int = Query(10, ge=1, le=200),
):
    return country_service.search_countries(search=search, limit=limit)


@router.get("/countries/{code}", response_model=CountrySchema)
async def get_country(code: str):
    country = country_service.get_country(code)
    if country is None:
        raise HTTPException(status_code=404, detail="Unknown country code")
    return country
