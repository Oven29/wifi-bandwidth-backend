from typing import List

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from src.api.dependencies import (
    get_activity_service,
    get_current_authenticated_user,
    get_current_user,
)
from src.schemas.network_activity import (
    FeedResponse,
    NetworkActivityPublish,
    NetworkActivityResponse,
)
from src.services.activity_service import ActivityService

router = APIRouter(prefix="/api/network-activities",
                   tags=["Network Activities"])


@router.get("", response_model=List[NetworkActivityResponse])
@router.get("/", response_model=List[NetworkActivityResponse])
async def list_activities(
    filter_traffic: int | None = None,
    current_user_id: int | None = Depends(get_current_user),
    activity_service: ActivityService = Depends(get_activity_service),
):
    """Retrieve published network activities with optional traffic filtering and ownership flag."""
    return await activity_service.get_published_activities(
        current_user_id=current_user_id,
        filter_traffic=filter_traffic,
    )


@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    activity_id: int | None = None,
    current_user_id: int | None = Depends(get_current_user),
    activity_service: ActivityService = Depends(get_activity_service),
):
    """Retrieve feed item with cyclic next ID, like status, and ownership flag."""
    return await activity_service.get_feed(
        current_user_id=current_user_id,
        activity_id=activity_id,
    )


@router.get("/draft", response_model=NetworkActivityResponse | None)
async def get_draft(
    current_user_id: int = Depends(get_current_authenticated_user),
    activity_service: ActivityService = Depends(get_activity_service),
):
    """Retrieve active draft for the authenticated user."""
    return await activity_service.get_user_draft(
        user_id=current_user_id,
    )


@router.post("", response_model=NetworkActivityResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=NetworkActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_draft(
    activity_title: str = Form(...),
    pic: UploadFile = File(...),
    video: UploadFile = File(...),
    current_user_id: int = Depends(get_current_authenticated_user),
    activity_service: ActivityService = Depends(get_activity_service),
):
    """Create a new activity draft with uploaded media files in MinIO."""
    return await activity_service.create_draft(
        user_id=current_user_id,
        activity_title=activity_title,
        pic=pic,
        video=video,
    )


@router.put("/{id}/publish", response_model=NetworkActivityResponse)
async def publish_activity(
    id: int,
    data: NetworkActivityPublish,
    current_user_id: int = Depends(get_current_authenticated_user),
    activity_service: ActivityService = Depends(get_activity_service),
):
    """Publish a draft network activity owned by authenticated user."""
    return await activity_service.publish_activity(
        user_id=current_user_id,
        activity_id=id,
        data=data,
    )


@router.delete("/{id}")
async def delete_activity(
    id: int,
    current_user_id: int = Depends(get_current_authenticated_user),
    activity_service: ActivityService = Depends(get_activity_service),
):
    """Soft delete an activity owned by authenticated user."""
    deleted_id = await activity_service.delete_activity(
        user_id=current_user_id,
        activity_id=id,
    )
    return {"message": "deleted", "id": deleted_id}


@router.post("/{id}/like")
async def toggle_like(
    id: int,
    current_user_id: int = Depends(get_current_authenticated_user),
    activity_service: ActivityService = Depends(get_activity_service),
):
    """Toggle like on an activity by authenticated user."""
    status_val = await activity_service.toggle_like(
        user_id=current_user_id,
        activity_id=id,
    )
    return {"status": status_val}
