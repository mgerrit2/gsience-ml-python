from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from src.routes import animals

import redis.asyncio as aioredis

from src.db.redis import init_redis, close_redis, get_redis

app = FastAPI(
    title="GScience API for testing AI models",
    description="Interactive FastAPI Docs",
    version="1.0.0",
)

# 2. Include endpoint routes (best practice: add prefix and tags)
# 2. Include the animals router
app.include_router(
    animals.router,
    prefix="/animals",
    tags=["Animals"],
)

# Specify the origins that are allowed to make requests to your API
origins = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://localhost:4200",
    "https://hoppscotch.io",  # Explicitly allow Hoppscotch Web UI
    "https://gscience-ai-ui.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # List of allowed origins
    allow_credentials=True,           # Allow cookies / authentication headers
    allow_methods=["*"],              # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],              # Allow all headers
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup: Open connection pool
    await init_redis()
    yield
    # 2. Shutdown: Close connection pool
    await close_redis()

@app.get("/")
def root():
    return {"message": "API is running"}

app = FastAPI(title="FastAPI Redis Integration", lifespan=lifespan)


# Example endpoint using FastAPI Dependency Injection
@app.get("/cache/{key}")
async def get_cache_value(
    key: str,
    redis: aioredis.Redis = Depends(get_redis)
):
    value = await redis.get(key)
    return {"key": key, "value": value}

@app.post("/cache/{key}")
async def set_cache_value(
    key: str,
    value: str,
    redis: aioredis.Redis = Depends(get_redis)
):
    await redis.set(key, value, ex=3600)  # Expires in 1 hour
    return {"status": "success", "key": key, "value": value}

