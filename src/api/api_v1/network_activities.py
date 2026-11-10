from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    get_current_authenticated_user,
    get_current_user,
)
from src.db.session import get_db
from src.schemas.network_activity import (
    FeedResponse,
    NetworkActivityPublish,
    NetworkActivityResponse,
)
from src.services.activity_service import ActivityService

router = APIRouter(prefix="/api/network-activities", tags=["Network Activities"])


@router.get("", response_model=list[NetworkActivityResponse])
@router.get("/", response_model=list[NetworkActivityResponse])
async def list_activities(
    filter_traffic: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: int | None = Depends(get_current_user),
):
    """Retrieve published network activities with optional traffic filtering and ownership flag."""
    return await ActivityService.get_published_activities(
        db=db,
        current_user_id=current_user_id,
        filter_traffic=filter_traffic,
    )


@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    activity_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: int | None = Depends(get_current_user),
):
    """Retrieve feed item with cyclic next ID, like status, and ownership flag."""
    return await ActivityService.get_feed(
        db=db,
        current_user_id=current_user_id,
        activity_id=activity_id,
    )


@router.get("/draft", response_model=NetworkActivityResponse | None)
async def get_draft(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_authenticated_user),
):
    """Retrieve active draft for the authenticated user."""
    return await ActivityService.get_user_draft(
        db=db,
        user_id=current_user_id,
    )


@router.post("", response_model=NetworkActivityResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=NetworkActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_draft(
    activity_title: str = Form(...),
    pic: UploadFile = File(...),
    video: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_authenticated_user),
):
    """Create a new activity draft with uploaded media files in MinIO."""
    return await ActivityService.create_draft(
        db=db,
        user_id=current_user_id,
        activity_title=activity_title,
        pic=pic,
        video=video,
    )


@router.put("/{id}/publish", response_model=NetworkActivityResponse)
async def publish_activity(
    id: int,
    data: NetworkActivityPublish,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_authenticated_user),
):
    """Publish a draft network activity owned by authenticated user."""
    return await ActivityService.publish_activity(
        db=db,
        user_id=current_user_id,
        activity_id=id,
        data=data,
    )


@router.delete("/{id}")
async def delete_activity(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_authenticated_user),
):
    """Soft delete an activity owned by authenticated user."""
    deleted_id = await ActivityService.delete_activity(
        db=db,
        user_id=current_user_id,
        activity_id=id,
    )
    return {"message": "deleted", "id": deleted_id}


@router.post("/{id}/like")
async def toggle_like(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_authenticated_user),
):
    """Toggle like on an activity by authenticated user."""
    status_val = await ActivityService.toggle_like(
        db=db,
        user_id=current_user_id,
        activity_id=id,
    )
    return {"status": status_val}
