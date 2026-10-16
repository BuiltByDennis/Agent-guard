import os
import time

import structlog
from dotenv import load_dotenv
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.metrics import DB_POOL_CHECKEDOUT

load_dotenv()

logger = structlog.get_logger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://user:password@localhost/proxy_db"
)
engine = create_async_engine(DATABASE_URL, echo=False, pool_size=5, max_overflow=5)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@event.listens_for(engine.sync_engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    DB_POOL_CHECKEDOUT.dec()


@event.listens_for(engine.sync_engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    DB_POOL_CHECKEDOUT.inc()


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.time())


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    start_time = conn.info["query_start_time"].pop()
    total = time.time() - start_time
    if total > 0.5:
        logger.warning("Slow Query", sql=statement, duration=total)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
