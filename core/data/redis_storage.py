from contextlib import asynccontextmanager
from typing import Annotated

from fastapi.params import Depends
from redis.asyncio.client import Redis
from starlette.requests import Request

from core.config_dir.config import redis_settings


@asynccontextmanager
async def get_redis_connection():
    redis = Redis(**redis_settings,  decode_responses=True)
    try:
        yield redis
    finally:
        await redis.close()

async def redis_pool(request: Request) -> Redis:
    return request.app.state.redis

RedisDep = Annotated[Redis, Depends(redis_pool)]