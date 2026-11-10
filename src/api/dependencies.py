from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.redis_client import get_user_by_session
from src.db.session import get_db
from src.repositories.activity_repository import ActivityRepository
from src.repositories.like_repository import LikeRepository
from src.repositories.user_repository import UserRepository
from src.services.activity_service import ActivityService
from src.services.user_service import UserService


# Cookie security scheme for Swagger UI integration
cookie_scheme = APIKeyCookie(name="session_id", auto_error=False)


async def get_current_user(session_id: str | None = Depends(cookie_scheme)) -> int | None:
    """Retrieve optional current user ID from session cookie."""
    if session_id is None:
        return None
    user_id = await get_user_by_session(session_id)
    return user_id


async def get_current_authenticated_user(
    user_id: int | None = Depends(get_current_user),
) -> int:
    """Ensure user is authenticated, otherwise raise HTTP 401."""
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user_id


# --- Репозитории ---

def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    """Provide UserRepository dependency."""
    return UserRepository(session=session)


def get_activity_repository(session: AsyncSession = Depends(get_db)) -> ActivityRepository:
    """Provide ActivityRepository dependency."""
    return ActivityRepository(session=session)


def get_like_repository(session: AsyncSession = Depends(get_db)) -> LikeRepository:
    """Provide LikeRepository dependency."""
    return LikeRepository(session=session)


# --- Сервисы ---

def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    """Provide UserService dependency configured with repositories."""
    return UserService(user_repo=user_repo)


def get_activity_service(
    activity_repo: ActivityRepository = Depends(get_activity_repository),
    like_repo: LikeRepository = Depends(get_like_repository),
) -> ActivityService:
    """Provide ActivityService dependency configured with repositories."""
    return ActivityService(activity_repo=activity_repo, like_repo=like_repo)
