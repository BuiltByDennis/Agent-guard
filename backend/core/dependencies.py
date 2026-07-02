import jwt
from fastapi import Request
from core.config import settings

def get_rate_limit_key(request: Request) -> str:
    # 1. Try authenticated user
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if "sub" in payload:
                return payload["sub"]
        except Exception:
            pass
            
    # 2. Try X-Forwarded-For
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
        
    # 3. Fallback to raw client IP
    return request.client.host if request.client else "127.0.0.1"

def get_agent_id(request: Request) -> str:
    return request.headers.get("X-Agent-ID", get_rate_limit_key(request))

def get_user_id(request: Request) -> str:
    return get_rate_limit_key(request)
