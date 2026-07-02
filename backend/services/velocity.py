import time
from core.config import settings
from core.redis import get_redis

async def check_cost_velocity(agent_id: str, new_cost: float) -> bool:
    """Checks if agent exceeded velocity. Returns True if exceeded."""
    redis_client = get_redis()
    if not redis_client:
        return False
        
    now = int(time.time())
    window_key = f"velocity:{agent_id}:{now // 60}"
    
    current_cost = await redis_client.get(window_key)
    if current_cost and float(current_cost) + new_cost > settings.VELOCITY_LIMIT:
        return True
        
    await redis_client.incrbyfloat(window_key, new_cost)
    await redis_client.expire(window_key, 120)
    return False

async def is_agent_suspended(agent_id: str) -> bool:
    redis_client = get_redis()
    if not redis_client:
        return False
    status = await redis_client.get(f"agent_status:{agent_id}")
    return status == "suspended"

async def suspend_agent(agent_id: str):
    redis_client = get_redis()
    if redis_client:
        await redis_client.set(f"agent_status:{agent_id}", "suspended")

async def unsuspend_agent(agent_id: str):
    redis_client = get_redis()
    if redis_client:
        await redis_client.delete(f"agent_status:{agent_id}")
