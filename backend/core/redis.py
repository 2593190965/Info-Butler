import redis.asyncio as aioredis

from backend.core.config import settings

redis_pool = aioredis.ConnectionPool.from_url(
    settings.redis_url,
    decode_responses=True,
)

redis_client = aioredis.Redis(connection_pool=redis_pool)


async def get_redis():
    return redis_client
