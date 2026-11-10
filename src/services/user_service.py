from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.redis_client import create_session, delete_session
from src.core.security import get_password_hash, verify_password
from src.models.user import User
from src.schemas.user import UserAuthRequest


class UserService:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        """Fetch user by primary key ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> User | None:
        """Fetch user by username."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @classmethod
    async def register_user(cls, db: AsyncSession, data: UserAuthRequest) -> User:
        """Register a new user with hashed password."""
        existing_user = await cls.get_by_username(db, data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        hashed_password = get_password_hash(data.password)
        user = User(username=data.username, password=hashed_password)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @classmethod
    async def authenticate_user(
        cls, db: AsyncSession, username: str, password: str
    ) -> tuple[User, str]:
        """Verify user credentials and create a session in Redis. Returns (user, session_id)."""
        user = await cls.get_by_username(db, username)
        if not user or not user.password or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid username or password",
            )

        session_id = await create_session(user.id)
        return user, session_id

    @staticmethod
    async def logout_user(session_id: str | None) -> None:
        """Revoke active session from Redis."""
        if session_id:
            await delete_session(session_id)
