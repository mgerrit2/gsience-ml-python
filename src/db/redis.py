import os
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://red-d8vea2r7uimc738bibmg:6379")

# Global client reference
redis_client: aioredis.Redis | None = None

async def init_redis() -> None:
    """Initialize Redis connection pool."""
    global redis_client
    redis_client = aioredis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20
    )

async def close_redis() -> None:
    """Close Redis connection pool cleanly."""
    global redis_client
    if redis_client:
        await redis_client.aclose()

def get_redis() -> aioredis.Redis:
    """Dependency provider / Getter for the Redis client."""
    if redis_client is None:
        raise RuntimeError("Redis connection is not initialized.")
    return redis_client