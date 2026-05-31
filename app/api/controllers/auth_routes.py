from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_schema import UserCreate
from app.core.security import get_password_hash, create_access_token

from app.api.dependencies import get_db
from app.services.user_service import authenticate_user, InactiveUserError
from app.core.security import create_access_token
from app.schemas.token_schema import Token

router = APIRouter()

@router.post("/test-security")
async def test_security_funcstion(user_in: UserCreate):
    hashed_pw = get_password_hash(user_in.password)
    token = create_access_token(data={"sub": user_in.email})
    
    return {
            "message": "Pass!",
            "email": user_in.email,
            "hashed_password": hashed_pw,
            "token": token
        }

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    try:
        user = await authenticate_user(db, email=form_data.username, password=form_data.password)
    except InactiveUserError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support.",
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}