from fastapi import APIRouter, Cookie, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from src.api.dependencies import get_user_service
from src.schemas.user import UserAuthRequest, UserResponse
from src.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserAuthRequest,
    user_service: UserService = Depends(get_user_service),
):
    """Register a new user."""
    return await user_service.register_user(data=data)


@router.post("/auth")
async def auth(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service),
):
    """Authenticate user, create session in Redis, and set session cookie."""
    _, session_id = await user_service.authenticate_user(
        username=form_data.username,
        password=form_data.password,
    )
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return {"message": "success", "session_id": session_id}


@router.post("/logout")
async def logout(
    response: Response,
    session_id: str | None = Cookie(default=None),
    user_service: UserService = Depends(get_user_service),
):
    """Log out user by deleting Redis session and clearing session cookie."""
    await user_service.logout_user(session_id=session_id)
    response.delete_cookie(key="session_id")
    return {"message": "logged out"}
