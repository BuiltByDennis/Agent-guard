import redis.asyncio as redis
from core.config import settings
import structlog

logger = structlog.get_logger(__name__)

redis_client = None

async def init_redis():
    global redis_client
    try:
        redis_client = redis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)
        await redis_client.ping()
        logger.info("redis_connected", url=settings.REDIS_URL)
    except Exception as e:
        logger.error("redis_connection_failed", error=str(e))
        redis_client = None

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("redis_closed")

def get_redis():
    return redis_client
