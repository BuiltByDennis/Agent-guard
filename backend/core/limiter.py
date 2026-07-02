from slowapi import Limiter
from core.dependencies import get_rate_limit_key

limiter = Limiter(key_func=get_rate_limit_key)
