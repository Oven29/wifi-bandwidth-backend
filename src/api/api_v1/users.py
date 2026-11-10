from fastapi import APIRouter, Cookie, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.schemas.user import UserAuthRequest, UserResponse
from src.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    return await UserService.register_user(db=db, data=data)


@router.post("/auth")
async def auth(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user, create session in Redis, and set session cookie."""
    _, session_id = await UserService.authenticate_user(
        db=db,
        username=form_data.username,
        password=form_data.password,
    )
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return {"message": "success", "session_id": session_id}


@router.post("/logout")
async def logout(
    response: Response,
    session_id: str | None = Cookie(default=None),
):
    """Log out user by deleting Redis session and clearing session cookie."""
    await UserService.logout_user(session_id=session_id)
    response.delete_cookie(key="session_id")
    return {"message": "logged out"}
