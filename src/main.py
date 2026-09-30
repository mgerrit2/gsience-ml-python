from contextlib import asynccontextmanager
from typing import Annotated, Literal, Any

from fastapi import FastAPI, Depends, Path, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as aioredis
from pydantic import BaseModel, Field
from redis import RedisError
from rich import status

from src.middleware.tracker import track_visitor
from src.routes import animals
from src.db.redis import init_redis, close_redis, get_redis

from slowapi import _rate_limit_exceeded_handler
from src.limiter import limiter  # Import from the separate file
from slowapi.errors import RateLimitExceeded

# 1. Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Open Redis connection pool
    await init_redis()
    yield
    # Shutdown: Close Redis connection pool
    await close_redis()

# 2. OpenAPI tags metadata for Swagger UI
tags_metadata = [
    {
        "name": "Animals",
        "description": "ONNX-powered image classification endpoints for identifying animal species.",
    },
]

# Request Schema
class CachePayload(BaseModel):
    data_type: Literal["string", "set", "hash", "list"] = Field(
        default="string",
        description="The Redis data structure to store"
    )
    value: Any = Field(
        ...,
        description="Value to store (str for string, list for set/list, dict for hash)"
    )
    ttl: int = Field(default=3600, ge=1, description="Expiration time in seconds")

# 3. Single FastAPI Instance
app = FastAPI(
    title="FastAPI GScience AI Integration",
    description="Dev FastAPI service for ONNX image classification and Redis visitor tracking.",
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
    contact={
        "name": "Gerrits marc",
        "email": "gerrits.marc@hotmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    dependencies=[Depends(track_visitor)]
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 4. Configure CORS Middleware
origins = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://localhost:4200",
    "https://hoppscotch.io",
    "https://gscience-ai-ui.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Include Routers
app.include_router(
    animals.router,
    prefix="/animals",
    tags=["Animals"],
)

# 6. Endpoints
@app.get("/")
def root():
    return {"message": "API is running"}

@app.get("/cache/{key}")
async def get_cache_value(
    key: Annotated[str, Path(description="The cache key to retrieve")],
    redis:Annotated[aioredis.Redis, Depends(get_redis)]
):
    # 1. Check if the key exists
    key_type = await redis.type(key)

    if key_type == "none":
        return {"key": key, "value": None, "type": "none"}

    # 2. Safely read based on Redis data type
    if key_type == "string":
        value = await redis.get(key)
    elif key_type == "set":
        value = list(await redis.smembers(key))
    elif key_type == "hash":
        value = await redis.hgetall(key)
    elif key_type == "list":
        value = await redis.lrange(key, 0, -1)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported Redis key type: {key_type}"
        )

    return {"key": key, "type": key_type, "value": value}

@app.post("/cache/{key}")
async def set_cache_value(
    key: Annotated[str, Path(description="The cache key to retrieve")],
    payload: CachePayload,
    redis: Annotated[aioredis.Redis, Depends(get_redis)]
):
    # 1. Delete key if it already exists with a different type
    existing_type = await redis.type(key)
    if existing_type != "none" and existing_type != payload.data_type:
        await redis.delete(key)

    # 2. Store data based on requested type
    try:
        if payload.data_type == "string":
            if not isinstance(payload.value, (str, int, float, bool)):
                raise ValueError("String type requires a primitive value (str/int/float/bool).")
            await redis.set(key, str(payload.value), ex=payload.ttl)

        elif payload.data_type == "set":
            if not isinstance(payload.value, list):
                raise ValueError("Set type requires a list of items.")
            await redis.sadd(key, *payload.value)
            await redis.expire(key, payload.ttl)

        elif payload.data_type == "hash":
            if not isinstance(payload.value, dict):
                raise ValueError("Hash type requires a dictionary/key-value object.")
            await redis.hset(key, mapping=payload.value)
            await redis.expire(key, payload.ttl)

        elif payload.data_type == "list":
            if not isinstance(payload.value, list):
                raise ValueError("List type requires a list of items.")
            # Clear existing list before pushing to ensure clean write
            await redis.delete(key)
            await redis.rpush(key, *payload.value)
            await redis.expire(key, payload.ttl)

    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err)
        )

    return {
        "status": "success",
        "key": key,
        "type": payload.data_type,
        "value": payload.value,
        "ttl": payload.ttl
    }


@app.get("/stats")
async def get_service_usage(redis: Annotated[aioredis.Redis, Depends(get_redis)]):
    """Returns total accesses and count of unique users safely defaulting to 0 on exception."""
    total_requests = 0
    unique_users = 0

    try:
        raw_requests = await redis.get("stats:total_requests")
        if raw_requests is not None:
            total_requests = int(raw_requests)
    except (RedisError, ValueError, TypeError):
        total_requests = 0

    try:
        unique_users = await redis.scard("stats:unique_visitors")
    except RedisError:
        unique_users = 0

    return {
        "total_requests": total_requests,
        "unique_users_tracked": unique_users,
    }