from typing import Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.like import Like
from src.repositories.base import BaseRepository


class LikeRepository(BaseRepository[Like]):
    """Repository handling database operations for Like entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(Like, session)

    async def get_by_user_and_activity(
        self, user_id: int, activity_id: int
    ) -> Like | None:
        """Fetch like entry by user and activity identifiers."""
        result = await self.session.execute(
            select(Like).where(
                Like.activity_id == activity_id,
                Like.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_by_activity(self, activity_id: int) -> int:
        """Count total likes for a given activity."""
        result = await self.session.execute(
            select(func.count(Like.id)).where(Like.activity_id == activity_id)
        )
        return result.scalar_one()

    async def get_likes_counts(self, activity_ids: Sequence[int]) -> dict[int, int]:
        """Batch fetch like counts for multiple activities to prevent N+1 queries."""
        if not activity_ids:
            return {}
        result = await self.session.execute(
            select(Like.activity_id, func.count(Like.id))
            .where(Like.activity_id.in_(activity_ids))
            .group_by(Like.activity_id)
        )
        counts = {activity_id: count for activity_id, count in result.all()}
        return {act_id: counts.get(act_id, 0) for act_id in activity_ids}

    async def create_like(self, user_id: int, activity_id: int) -> Like:
        """Create and persist a new like."""
        like = Like(user_id=user_id, activity_id=activity_id)
        return await self.create(like)
