import uuid
from redis.asyncio import from_url, Redis

from src.core.config import settings

# Initialize async Redis client
redis_client: Redis = from_url(settings.redis.url, decode_responses=True)

SESSION_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days (604800 seconds)

# Atomic Lua script to retrieve user_id and refresh TTL simultaneously
LUA_GET_AND_REFRESH_SESSION = """
local user_id = redis.call('GET', KEYS[1])
if user_id then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return user_id
"""


async def create_session(user_id: int) -> str:
    """Generate session UUID and save user_id to Redis with 7 days TTL."""
    session_id = uuid.uuid4().hex
    await redis_client.setex(session_id, SESSION_TTL_SECONDS, str(user_id))
    return session_id


async def get_user_by_session(session_id: str) -> int | None:
    """Retrieve user_id from Redis and refresh TTL atomically using Lua EVAL."""
    user_id = await redis_client.eval(
        LUA_GET_AND_REFRESH_SESSION,
        1,
        session_id,
        SESSION_TTL_SECONDS,
    )
    if user_id is None:
        return None
    return int(user_id)


async def delete_session(session_id: str) -> None:
    """Delete session key from Redis."""
    await redis_client.delete(session_id)
