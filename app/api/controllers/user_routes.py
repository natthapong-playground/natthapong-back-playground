from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_model import User
from app.schemas.user_schema import UserCreate, UserResponse
from app.services import user_service
from app.api.dependencies import get_current_user, get_db

router = APIRouter()

# CREATE
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
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