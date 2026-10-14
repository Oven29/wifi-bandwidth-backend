from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie

from src.core.redis_client import get_user_by_session

# Cookie security scheme for Swagger UI integration
cookie_scheme = APIKeyCookie(name="session_id", auto_error=False)


async def get_current_user(session_id: str = Depends(cookie_scheme)) -> int | None:
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
