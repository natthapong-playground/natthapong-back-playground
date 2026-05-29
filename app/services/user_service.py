from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user_model import User
from app.schemas.user_schema import UserCreate
from app.core.security import get_password_hash, verify_password

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    # searchs user by email
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        role=user_in.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user

async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    # Verifies user login attempt
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    
    return user