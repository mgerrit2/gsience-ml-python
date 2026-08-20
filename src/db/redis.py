import os
import redis.asyncio as aioredis

# Read environment variable with a safe fallback
raw_url = os.getenv("REDIS_URL")

# Fallback if raw_url is missing, empty, or None
if not raw_url or not raw_url.strip():
    REDIS_URL = "redis://127.0.0.1:6379/0"
else:
    REDIS_URL = raw_url.strip().strip("'\"")  # Strip whitespace and extraQuotes

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