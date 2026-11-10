from typing import Sequence
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.network_activity import ActivityStatus, NetworkActivity
from src.repositories.base import BaseRepository


class ActivityRepository(BaseRepository[NetworkActivity]):
    """Repository handling database operations for NetworkActivity entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(NetworkActivity, session)

    async def get_published_activities(
        self, filter_traffic: int | None = None
    ) -> Sequence[NetworkActivity]:
        """Fetch published activities, optionally filtered by maximum traffic."""
        stmt = (
            select(NetworkActivity)
            .where(NetworkActivity.status == ActivityStatus.PUBLISHED)
            .order_by(NetworkActivity.id.asc())
        )
        if filter_traffic is not None:
            stmt = stmt.where(NetworkActivity.average_traffic_mbps <= filter_traffic)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_feed_activity(
        self, activity_id: int | None = None
    ) -> NetworkActivity | None:
        """Fetch single published activity for feed, falling back to the first available."""
        if activity_id is not None:
            result = await self.session.execute(
                select(NetworkActivity)
                .where(
                    NetworkActivity.id == activity_id,
                    NetworkActivity.status == ActivityStatus.PUBLISHED,
                )
                .limit(1)
            )
            activity = result.scalar_one_or_none()
            if activity:
                return activity

        result = await self.session.execute(
            select(NetworkActivity)
            .where(NetworkActivity.status == ActivityStatus.PUBLISHED)
            .order_by(NetworkActivity.id.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_next_published_id(self, current_id: int) -> int | None:
        """Get the ID of the next published activity, looping to the beginning if at the end."""
        next_result = await self.session.execute(
            select(NetworkActivity.id)
            .where(
                NetworkActivity.id > current_id,
                NetworkActivity.status == ActivityStatus.PUBLISHED,
            )
            .order_by(NetworkActivity.id.asc())
            .limit(1)
        )
        next_id = next_result.scalar_one_or_none()
        if next_id is not None:
            return next_id

        wrap_result = await self.session.execute(
            select(NetworkActivity.id)
            .where(NetworkActivity.status == ActivityStatus.PUBLISHED)
            .order_by(NetworkActivity.id.asc())
            .limit(1)
        )
        return wrap_result.scalar_one_or_none()

    async def get_user_draft(self, user_id: int) -> NetworkActivity | None:
        """Fetch the most recent draft activity created by user."""
        result = await self.session.execute(
            select(NetworkActivity)
            .where(
                NetworkActivity.creator_id == user_id,
                NetworkActivity.status == ActivityStatus.DRAFT,
            )
            .order_by(NetworkActivity.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def soft_delete(self, activity: NetworkActivity) -> None:
        """Soft delete by updating status to DELETED."""
        activity.status = ActivityStatus.DELETED
        await self.session.commit()

    async def soft_delete_by_id(self, activity_id: int) -> None:
        """Soft delete activity by ID directly."""
        update_query = """
            UPDATE network_activities 
            SET status = 'DELETED' 
            WHERE id = :id
        """
        await self.session.execute(text(update_query), {"id": activity_id})
        await self.session.commit()
