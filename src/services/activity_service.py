from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.minio_client import upload_file_to_minio
from src.models.like import Like
from src.models.network_activity import ActivityStatus, NetworkActivity
from src.schemas.network_activity import (
    NetworkActivityPublish,
    NetworkActivityResponse,
)


class ActivityService:
    @staticmethod
    async def get_published_activities(
        db: AsyncSession,
        current_user_id: int | None = None,
        filter_traffic: int | None = None,
    ) -> list[NetworkActivityResponse]:
        """Fetch all published activities, optionally filtered by traffic, calculating ownership."""
        stmt = (
            select(NetworkActivity)
            .where(NetworkActivity.status == ActivityStatus.PUBLISHED)
            .order_by(NetworkActivity.id.asc())
        )
        if filter_traffic is not None:
            stmt = stmt.where(NetworkActivity.average_traffic_mbps <= filter_traffic)

        result = await db.execute(stmt)
        activities = result.scalars().all()

        response = []
        for act in activities:
            item = NetworkActivityResponse.model_validate(act)
            item.is_owner = (
                1 if current_user_id is not None and act.creator_id == current_user_id else 0
            )
            response.append(item)
        return response

    @staticmethod
    async def get_feed(
        db: AsyncSession,
        current_user_id: int | None = None,
        activity_id: int | None = None,
    ) -> dict:
        """Fetch an activity for feed view with cyclic pagination, ownership, and like status."""
        active_activity = None
        if activity_id is not None:
            result = await db.execute(
                select(NetworkActivity)
                .where(
                    NetworkActivity.id == activity_id,
                    NetworkActivity.status == ActivityStatus.PUBLISHED,
                )
                .limit(1)
            )
            active_activity = result.scalar_one_or_none()

        if active_activity is None:
            result = await db.execute(
                select(NetworkActivity)
                .where(NetworkActivity.status == ActivityStatus.PUBLISHED)
                .order_by(NetworkActivity.id.asc())
                .limit(1)
            )
            active_activity = result.scalar_one_or_none()

        if not active_activity:
            return {
                "activity": None,
                "next_id": None,
                "next_activity_id": None,
            }

        next_result = await db.execute(
            select(NetworkActivity.id)
            .where(
                NetworkActivity.id > active_activity.id,
                NetworkActivity.status == ActivityStatus.PUBLISHED,
            )
            .order_by(NetworkActivity.id.asc())
            .limit(1)
        )
        next_activity_id = next_result.scalar_one_or_none()

        if next_activity_id is None:
            wrap_result = await db.execute(
                select(NetworkActivity.id)
                .where(NetworkActivity.status == ActivityStatus.PUBLISHED)
                .order_by(NetworkActivity.id.asc())
                .limit(1)
            )
            next_activity_id = wrap_result.scalar_one_or_none()

        existing_like = None
        if current_user_id is not None:
            like_result = await db.execute(
                select(Like).where(
                    Like.activity_id == active_activity.id,
                    Like.user_id == current_user_id,
                )
            )
            existing_like = like_result.scalar_one_or_none()

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

    @staticmethod
    async def get_user_draft(
        db: AsyncSession,
        user_id: int,
    ) -> NetworkActivityResponse | None:
        """Fetch the latest active draft created by user."""
        result = await db.execute(
            select(NetworkActivity)
            .where(
                NetworkActivity.creator_id == user_id,
                NetworkActivity.status == ActivityStatus.DRAFT,
            )
            .order_by(NetworkActivity.id.desc())
            .limit(1)
        )
        draft = result.scalar_one_or_none()
        if not draft:
            return None

        resp = NetworkActivityResponse.model_validate(draft)
        resp.is_owner = 1
        return resp

    @staticmethod
    async def create_draft(
        db: AsyncSession,
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
        db.add(new_activity)
        await db.commit()
        await db.refresh(new_activity)

        resp = NetworkActivityResponse.model_validate(new_activity)
        resp.is_owner = 1
        return resp

    @staticmethod
    async def publish_activity(
        db: AsyncSession,
        user_id: int,
        activity_id: int,
        data: NetworkActivityPublish,
    ) -> NetworkActivityResponse:
        """Publish an existing draft activity owned by user."""
        result = await db.execute(
            select(NetworkActivity).where(NetworkActivity.id == activity_id)
        )
        activity = result.scalar_one_or_none()
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

        await db.commit()
        await db.refresh(activity)

        resp = NetworkActivityResponse.model_validate(activity)
        resp.is_owner = 1
        return resp

    @staticmethod
    async def delete_activity(
        db: AsyncSession,
        user_id: int,
        activity_id: int,
    ) -> int:
        """Soft delete an activity owned by user."""
        result = await db.execute(
            select(NetworkActivity).where(NetworkActivity.id == activity_id)
        )
        activity = result.scalar_one_or_none()
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

        activity.status = ActivityStatus.DELETED
        await db.commit()
        return activity_id

    @staticmethod
    async def toggle_like(
        db: AsyncSession,
        user_id: int,
        activity_id: int,
    ) -> int:
        """Toggle like state for an activity by authenticated user. Returns 1 if added, 0 if removed."""
        act_result = await db.execute(
            select(NetworkActivity).where(NetworkActivity.id == activity_id)
        )
        activity = act_result.scalar_one_or_none()
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found",
            )

        like_result = await db.execute(
            select(Like).where(
                Like.activity_id == activity_id,
                Like.user_id == user_id,
            )
        )
        existing_like = like_result.scalar_one_or_none()

        if existing_like:
            await db.delete(existing_like)
            await db.commit()
            return 0

        new_like = Like(user_id=user_id, activity_id=activity_id)
        db.add(new_like)
        await db.commit()
        return 1
