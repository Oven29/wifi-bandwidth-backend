from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.models.user import User
from src.schemas.user import UserAuthRequest, UserResponse

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == data.username))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    user = User(username=data.username)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/auth")
async def auth(data: UserAuthRequest | None = None):
    return {"message": "success", "token": "stub"}


@router.post("/logout")
async def logout():
    return {"message": "logged out"}
