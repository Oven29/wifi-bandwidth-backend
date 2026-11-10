from fastapi import HTTPException, status

from src.core.redis_client import create_session, delete_session
from src.core.security import get_password_hash, verify_password
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserAuthRequest


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_by_id(self, user_id: int) -> User | None:
        """Fetch user by primary key ID."""
        return await self.user_repo.get_by_id(user_id)

    async def get_by_username(self, username: str) -> User | None:
        """Fetch user by username."""
        return await self.user_repo.get_by_username(username)

    async def register_user(self, data: UserAuthRequest) -> User:
        """Register a new user with hashed password."""
        existing_user = await self.user_repo.get_by_username(data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        hashed_password = get_password_hash(data.password)
        return await self.user_repo.create_user(
            username=data.username,
            password_hash=hashed_password,
        )

    async def authenticate_user(
        self, username: str, password: str
    ) -> tuple[User, str]:
        """Verify user credentials and create a session in Redis. Returns (user, session_id)."""
        user = await self.user_repo.get_by_username(username)
        if not user or not user.password or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid username or password",
            )

        session_id = await create_session(user.id)
        return user, session_id

    async def logout_user(self, session_id: str | None) -> None:
        """Revoke active session from Redis."""
        if session_id:
            await delete_session(session_id)
