import json
import structlog
from sqlalchemy import text
from database import AsyncSessionLocal
from models import InteractionSpan
from core.redis import get_redis

logger = structlog.get_logger(__name__)

async def save_interaction_to_db(span_data: dict):
    try:
        tenant_id = span_data.get("tenant_id")
        async with AsyncSessionLocal() as session:
            if tenant_id:
                await session.execute(
                    text("SET LOCAL app.current_tenant = :tenant_id"),
                    {"tenant_id": str(tenant_id)}
                )
            new_span = InteractionSpan(**span_data)
            session.add(new_span)
            await session.commit()
    except Exception as e:
        logger.error("db_save_failed", error=str(e), tenant_id=span_data.get("tenant_id"), agent_id=span_data.get("agent_id"))
        try:
            redis = get_redis()
            if redis:
                await redis.lpush("telemetry_dlq", json.dumps(span_data))
                logger.info("telemetry_pushed_to_dlq")
        except Exception as redis_e:
            logger.error("dlq_push_failed", error=str(redis_e))
