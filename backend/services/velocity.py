import time
from core.config import settings
from core.redis import get_redis

async def check_cost_velocity(agent_id: str, new_cost: float) -> bool:
    """Checks if agent exceeded velocity. Returns True if exceeded."""
    redis_client = get_redis()
    if not redis_client:
        return True  # Fail CLOSED - block agent if Redis is down
        
    now = int(time.time())
    window_key = f"velocity:{agent_id}:{now // 60}"
    
    lua_script = """
    local current = redis.call("GET", KEYS[1])
    if current and tonumber(current) + tonumber(ARGV[1]) > tonumber(ARGV[2]) then
        return 1
    end
    redis.call("INCRBYFLOAT", KEYS[1], ARGV[1])
    redis.call("EXPIRE", KEYS[1], 120)
    return 0
    """
    is_exceeded = await redis_client.eval(lua_script, 1, window_key, new_cost, settings.VELOCITY_LIMIT)
    return bool(is_exceeded)

async def is_agent_suspended(agent_id: str) -> bool:
    redis_client = get_redis()
    if not redis_client:
        return True  # Fail CLOSED - block agent if Redis is down
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
