from typing import List

from fastapi import HTTPException, UploadFile, status

from src.core.minio_client import upload_file_to_minio
from src.models.network_activity import ActivityStatus, NetworkActivity
from src.repositories.activity_repository import ActivityRepository
from src.repositories.like_repository import LikeRepository
from src.schemas.network_activity import (
    NetworkActivityPublish,
    NetworkActivityResponse,
)


class ActivityService:
    """Service handling business logic for network activities."""

    def __init__(
        self,
        activity_repo: ActivityRepository,
        like_repo: LikeRepository,
    ):
        self.activity_repo = activity_repo
        self.like_repo = like_repo

    async def get_published_activities(
        self,
        current_user_id: int | None = None,
        filter_traffic: int | None = None,
    ) -> List[NetworkActivityResponse]:
        """Fetch all published activities, optionally filtered by traffic, calculating ownership."""
        activities = await self.activity_repo.get_published_activities(filter_traffic)

        response = []
        for act in activities:
            item = NetworkActivityResponse.model_validate(act)
            item.is_owner = (
                1 if current_user_id is not None and act.creator_id == current_user_id else 0
            )
            response.append(item)
        return response

    async def get_feed(
        self,
        current_user_id: int | None = None,
        activity_id: int | None = None,
    ) -> dict:
        """Fetch an activity for feed view with cyclic pagination, ownership, and like status."""
        active_activity = await self.activity_repo.get_feed_activity(activity_id)

        if not active_activity:
            return {
                "activity": None,
                "next_id": None,
                "next_activity_id": None,
            }

        next_activity_id = await self.activity_repo.get_next_published_id(active_activity.id)

        existing_like = None
        if current_user_id is not None:
            existing_like = await self.like_repo.get_by_user_and_activity(
                user_id=current_user_id,
                activity_id=active_activity.id,
            )

        activity_resp = NetworkActivityResponse.model_validate(active_activity)
        activity_resp.is_owner = (
            1 if current_user_id is not None and active_activity.creator_id == current_user_id else 0
        )
        activity_resp.is_liked = 1 if existing_like else 0

        return {
            "activity": activity_resp,
            "next_id": next_activity_id,
            "next_activity_id": next_activity_id,
        }

    async def get_user_draft(
        self,
        user_id: int,
    ) -> NetworkActivityResponse | None:
        """Fetch the latest active draft created by user."""
        draft = await self.activity_repo.get_user_draft(user_id)
        if not draft:
            return None

        resp = NetworkActivityResponse.model_validate(draft)
        resp.is_owner = 1
        return resp

    async def create_draft(
        self,
        user_id: int,
        activity_title: str,
        pic: UploadFile,
        video: UploadFile,
    ) -> NetworkActivityResponse:
        """Upload media to MinIO and persist a new draft activity belonging to authenticated user."""
        image_url = upload_file_to_minio(pic)
        video_url = upload_file_to_minio(video)

        new_activity = NetworkActivity(
            activity_title=activity_title,
            activity_description="",
            average_traffic_mbps=0,
            max_latency_ms=0,
            preview_image_url=image_url,
            preview_video_url=video_url,
            status=ActivityStatus.DRAFT,
            creator_id=user_id,
        )
        saved_activity = await self.activity_repo.create(new_activity)

        resp = NetworkActivityResponse.model_validate(saved_activity)
        resp.is_owner = 1
        return resp

    async def publish_activity(
        self,
        user_id: int,
        activity_id: int,
        data: NetworkActivityPublish,
    ) -> NetworkActivityResponse:
        """Publish an existing draft activity owned by user."""
        activity = await self.activity_repo.get_by_id(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found",
            )

        if activity.creator_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the owner of this activity",
            )

        if activity.status == ActivityStatus.DELETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot publish a deleted activity",
            )

        activity.activity_description = data.activity_description or data.description or ""
        activity.average_traffic_mbps = data.average_traffic_mbps
        activity.max_latency_ms = data.max_latency_ms
        activity.status = ActivityStatus.PUBLISHED

        updated_activity = await self.activity_repo.update(activity)

        resp = NetworkActivityResponse.model_validate(updated_activity)
        resp.is_owner = 1
        return resp

    async def delete_activity(
        self,
        user_id: int,
        activity_id: int,
    ) -> int:
        """Soft delete an activity owned by user."""
        activity = await self.activity_repo.get_by_id(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found",
            )

        if activity.creator_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the owner of this activity",
            )

        await self.activity_repo.soft_delete(activity)
        return activity_id

    async def toggle_like(
        self,
        user_id: int,
        activity_id: int,
    ) -> int:
        """Toggle like state for an activity by authenticated user. Returns 1 if added, 0 if removed."""
        activity = await self.activity_repo.get_by_id(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found",
            )

        existing_like = await self.like_repo.get_by_user_and_activity(
            user_id=user_id,
            activity_id=activity_id,
        )

        if existing_like:
            await self.like_repo.delete(existing_like)
            return 0

        await self.like_repo.create_like(user_id=user_id, activity_id=activity_id)
        return 1
