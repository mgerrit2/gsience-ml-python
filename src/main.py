from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Depends, Path
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as aioredis

from src.middleware.tracker import track_visitor
from src.routes import animals
from src.db.redis import init_redis, close_redis, get_redis

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
    value = await redis.get(key)
    return {"key": key, "value": value}

@app.post("/cache/{key}")
async def set_cache_value(
    key: Annotated[str, Path(description="The cache key to retrieve")],
    value: str,
    redis: Annotated[aioredis.Redis, Depends(get_redis)]
):
    await redis.set(key, value, ex=3600)  # Expires in 1 hour
    return {"status": "success", "key": key, "value": value}


@app.get("/stats")
async def get_service_usage(redis: Annotated[aioredis.Redis, Depends(get_redis)]):
    """Returns total accesses and count of unique users."""
    total_requests = await redis.get("stats:total_requests") or 0
    unique_users = await redis.scard("stats:unique_visitors") or 0

    return {
        "total_requests": int(total_requests),
        "unique_users_tracked": unique_users,
    }