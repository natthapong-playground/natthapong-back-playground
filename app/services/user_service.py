from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user_model import User
from app.schemas.user_schema import UserCreate
from app.core.security import get_password_hash, verify_password

GOOGLE_IDENTITY_PREFIX = "google:"


class GoogleAccountConflictError(Exception):
    pass


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    # searchs user by email
    result = await db.execute(select(User).where(func.lower(User.email) == email.lower()))
    return result.scalars().first()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        role=user_in.role,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


def _google_identity_marker(subject: str) -> str:
    return f"{GOOGLE_IDENTITY_PREFIX}{subject}"


def _require_matching_google_identity(user: User, subject: str) -> User:
    if user.hashed_password != _google_identity_marker(subject):
        raise GoogleAccountConflictError()
    return user


async def get_user_by_google_subject(db: AsyncSession, subject: str) -> User | None:
    result = await db.execute(
        select(User).where(User.hashed_password == _google_identity_marker(subject))
    )
    return result.scalars().first()


async def get_or_create_google_user(db: AsyncSession, email: str, subject: str) -> User:
    user = await get_user_by_google_subject(db, subject)
    if user:
        return user

    user = await get_user_by_email(db, email)
    if user:
        return _require_matching_google_identity(user, subject)

    db_user = User(
        email=email,
        hashed_password=_google_identity_marker(subject),
        role="Regular",
    )
    db.add(db_user)
    try:
        await db.commit()
    except IntegrityError:
        # A concurrent first login may have created the same account.
        await db.rollback()
        user = await get_user_by_email(db, email)
        if user:
            return _require_matching_google_identity(user, subject)
        raise

    await db.refresh(db_user)
    return db_user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    # Verifies user login attempt
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if user.hashed_password.startswith(GOOGLE_IDENTITY_PREFIX):
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        raise InactiveUserError()
    return user


class InactiveUserError(Exception):
    pass
