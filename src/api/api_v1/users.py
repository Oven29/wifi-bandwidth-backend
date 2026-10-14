from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.redis_client import create_session, delete_session
from src.core.security import get_password_hash, verify_password
from src.db.session import get_db
from src.models.user import User
from src.schemas.user import UserAuthRequest, UserResponse

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user with hashed password."""
    result = await db.execute(select(User).where(User.username == data.username))
    existing_user = result.scalar_one_or_none()
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


@router.post("/auth")
async def auth(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user with username and password, create session in Redis, and set session cookie."""
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not user.password or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password",
        )

    session_id = await create_session(user.id)
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return {"message": "success", "session_id": session_id}


@router.post("/logout")
async def logout(
    response: Response,
    session_id: str | None = Cookie(default=None),
):
    """Log out user by deleting Redis session and clearing session cookie."""
    if session_id:
        await delete_session(session_id)
    response.delete_cookie(key="session_id")
    return {"message": "logged out"}
