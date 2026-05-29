from fastapi import APIRouter
from app.schemas.user_schema import UserCreate
from app.core.security import get_password_hash, create_access_token

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