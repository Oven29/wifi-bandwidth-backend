import uuid
from redis.asyncio import from_url, Redis

from src.core.config import settings

# Initialize async Redis client
redis_client: Redis = from_url(settings.REDIS_URL, decode_responses=True)

SESSION_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days TTL


async def create_session(user_id: int) -> str:
    """Generate session UUID and save user_id to Redis with 7 days TTL."""
    session_id = uuid.uuid4().hex
    await redis_client.setex(session_id, SESSION_TTL_SECONDS, str(user_id))
    return session_id


async def get_user_by_session(session_id: str) -> int | None:
    """Retrieve user_id from Redis using session UUID."""
    user_id = await redis_client.get(session_id)
    if user_id is None:
        return None
    return int(user_id)


async def delete_session(session_id: str) -> None:
    """Delete session key from Redis."""
    await redis_client.delete(session_id)
