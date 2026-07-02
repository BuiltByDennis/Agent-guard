import os
import logging
import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from prometheus_fastapi_instrumentator import Instrumentator

import sentry_sdk
import structlog

from core.config import settings
from core.redis import init_redis, close_redis, get_redis
from core.http_client import init_http_client, close_http_client
from core.limiter import limiter
from database import get_db, engine
from init_db import init_db as initialize_database

from routers.auth import router as auth_router
from routers.proxy import router as proxy_router
from routers.agents import router as agents_router
from routers.admin import router as admin_router
from routers.telemetry import router as telemetry_router
from services.telemetry import save_interaction_to_db

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
    )

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False
)
logger = structlog.get_logger(__name__)

async def dlq_worker():
    while True:
        try:
            redis_client = get_redis()
            if redis_client:
                item = await redis_client.brpop("telemetry_dlq", timeout=5)
                if item:
                    _, data = item
                    span_data = json.loads(data)
                    await save_interaction_to_db(span_data)
            else:
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("dlq_worker_error", error=str(e))
            await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_database()
    await init_redis()
    redis_client = get_redis()
    if redis_client:
        FastAPICache.init(RedisBackend(redis_client), prefix="agent-proxy-cache")
    await init_http_client()
    dlq_task = asyncio.create_task(dlq_worker())
    yield
    dlq_task.cancel()
    await close_http_client()
    await close_redis()

app = FastAPI(title="Agent Proxy", lifespan=lifespan)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

@app.middleware("http")
async def tracing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    # Skip CSRF check for auth endpoints (token, refresh, logout are handled separately)
    if request.url.path in ["/v1/auth/token", "/v1/auth/refresh", "/v1/auth/logout"]:
        return await call_next(request)
    
    if request.method in ["POST", "PATCH", "DELETE", "PUT"]:
        csrf_cookie = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("X-CSRF-Token")
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            return Response(status_code=403, content="CSRF Token Missing or Invalid")
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Agent-ID", "X-Agent-Type", "X-API-Key"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router)
app.include_router(proxy_router)
app.include_router(agents_router)
app.include_router(admin_router)
app.include_router(telemetry_router)

@app.get("/health")
async def health_check(response: Response, db: AsyncSession = Depends(get_db)):
    status = {"status": "ok", "db": "ok", "redis": "ok"}
    try:
        await db.execute(text("SELECT 1"))
        pool = engine.pool
        status["db_pool"] = {
            "size": pool.size(),
            "checkedin": pool.checkedin(),
            "overflow": pool.overflow(),
            "checkedout": pool.checkedout()
        }
    except Exception as e:
        logger.error("health_check_db_failed", error=str(e))
        status["db"] = "error"
        status["status"] = "error"
    
    try:
        redis_client = get_redis()
        if redis_client:
            await redis_client.ping()
        else:
            status["redis"] = "disconnected"
    except Exception as e:
        logger.warning("health_check_redis_failed", error=str(e))
        status["redis"] = "error"

    if status["status"] == "error":
        response.status_code = 503
    return status
