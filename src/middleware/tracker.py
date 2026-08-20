from typing import Annotated
from fastapi import Request, Depends
import redis.asyncio as aioredis
from src.db.redis import get_redis


async def track_visitor(request: Request, redis: Annotated[aioredis.Redis, Depends(get_redis)]):
    """Tracks overall request count and unique visitor IPs in Redis."""
    # 1. Get client IP address
    client_ip = request.client.host if request.client else "unknown"

    # Handle reverse proxies (e.g., Render, Nginx, Cloudflare)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    # 2. Increment total requests
    await redis.incr("stats:total_requests")

    # 3. Add client IP to a set of unique visitors
    await redis.sadd("stats:unique_visitors", client_ip)