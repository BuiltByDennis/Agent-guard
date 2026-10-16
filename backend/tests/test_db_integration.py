"""Real-database integration tests (Phase 1).

These tests prove the things the mocked suite cannot:

1. `alembic upgrade head` converges a FRESH database to the model schema
   (and is safe to run twice).
2. Row-Level Security actually isolates tenants when the app connects as
   a non-superuser role — including the agent API-key lookup flag, and
   audit_logs visibility.
3. The full API flow works against the real schema: login -> create agent
   -> proxied call (upstream mocked) -> span persisted -> dashboard
   summary sees exactly that tenant's data.

Required environment (otherwise the module is skipped):
- TEST_DATABASE_URL: admin/owner asyncpg URL (migrations, seeding, checks)
- DATABASE_URL: the app-role asyncpg URL. This MUST be a non-superuser,
  non-owner role — superusers bypass RLS even with FORCE, which would make
  the isolation assertions meaningless. The module fixture creates the
  role `agentguard_app` (password: TEST_APP_PASSWORD, default "apppass")
  and grants it table access; DATABASE_URL must point at that role.
- REDIS_URL is not needed: velocity checks are patched out (Redis
  behaviour is covered by the unit tests); the auth lockout/blocklist are
  None-safe without Redis.
"""

import asyncio
import json
import os
import subprocess
import sys
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

ADMIN_URL = os.getenv("TEST_DATABASE_URL")
APP_PASSWORD = os.getenv("TEST_APP_PASSWORD", "apppass")

pytestmark = pytest.mark.skipif(
    not ADMIN_URL, reason="TEST_DATABASE_URL not set — real-DB tests skipped"
)

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(autouse=True)
def _real_dependencies():
    """These tests exercise the real dependency graph. Other test modules
    install app.dependency_overrides at import time (e.g. test_api.py) and
    never clear them, which would silently hand this module mocked DB
    sessions. Clear them for each test here and restore afterwards."""
    from main import app

    saved = dict(app.dependency_overrides)
    app.dependency_overrides = {}
    yield
    app.dependency_overrides = saved


def make_admin_engine():
    return create_async_engine(ADMIN_URL)


def run_migrations():
    """alembic upgrade head, as the admin/owner role, twice (idempotent)."""
    env = dict(os.environ, DATABASE_URL=ADMIN_URL)
    for _ in range(2):
        proc = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=BACKEND_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.fixture(scope="module", autouse=True)
def migrated_db():
    run_migrations()

    async def _setup():
        engine = make_admin_engine()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'agentguard_app') THEN "
                    f"CREATE ROLE agentguard_app LOGIN PASSWORD '{APP_PASSWORD}'; "
                    "END IF; END $$;"
                )
            )
            await conn.execute(
                text(
                    "GRANT SELECT, INSERT, UPDATE, DELETE "
                    "ON ALL TABLES IN SCHEMA public TO agentguard_app"
                )
            )
            await conn.execute(
                text(
                    "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public "
                    "TO agentguard_app"
                )
            )
        await engine.dispose()

    asyncio.run(_setup())
    yield


async def _seed_tenant(conn, email: str) -> uuid.UUID:
    uid = uuid.uuid4()
    await conn.execute(
        text(
            "INSERT INTO users (id, email, hashed_password, role) "
            "VALUES (:id, :email, 'x', 'admin')"
        ),
        {"id": str(uid), "email": email},
    )
    return uid


@pytest.mark.asyncio
async def test_migrations_converge_schema_to_models():
    from models import Base

    engine = make_admin_engine()
    async with engine.connect() as conn:
        rows = await conn.execute(
            text(
                "SELECT table_name, column_name FROM information_schema.columns "
                "WHERE table_schema = 'public'"
            )
        )
        db_cols = {}
        for table_name, column_name in rows:
            db_cols.setdefault(table_name, set()).add(column_name)
    await engine.dispose()

    for table in Base.metadata.tables.values():
        assert table.name in db_cols, f"missing table {table.name}"
        missing = {c.name for c in table.columns} - db_cols[table.name]
        assert not missing, f"{table.name} missing columns {missing}"


@pytest.mark.asyncio
async def test_rls_tenant_isolation():
    admin_engine = make_admin_engine()
    app_engine = create_async_engine(os.environ["DATABASE_URL"])
    app_sessions = async_sessionmaker(app_engine, expire_on_commit=False)
    suffix = uuid.uuid4().hex[:8]
    email_a, email_b = f"a-{suffix}@t.dev", f"b-{suffix}@t.dev"
    agent_id = f"agent-{suffix}"

    async with admin_engine.begin() as conn:
        tenant_a = await _seed_tenant(conn, email_a)
        tenant_b = await _seed_tenant(conn, email_b)
        # One agent + one span + one audit row, owned by tenant A
        await conn.execute(
            text(
                "INSERT INTO agents (tenant_id, agent_id, name, hashed_api_key, is_active) "
                "VALUES (:t, :a, 'A agent', 'hash', true)"
            ),
            {"t": str(tenant_a), "a": agent_id},
        )
        await conn.execute(
            text(
                "INSERT INTO spans (tenant_id, agent_id, agent_type, latency_ms, "
                "tokens_used, cost, status_code) "
                "VALUES (:t, :a, 'general', 10, 5, 0.01, 200)"
            ),
            {"t": str(tenant_a), "a": agent_id},
        )
        await conn.execute(
            text(
                "INSERT INTO audit_logs (tenant_id, performed_by, action) "
                "VALUES (:t, :t, 'agent_created')"
            ),
            {"t": str(tenant_a)},
        )
    await admin_engine.dispose()

    async def count_as(tenant, sql, params=None):
        async with app_sessions() as session:
            async with session.begin():
                if tenant is not None:
                    await session.execute(
                        text(f"SET LOCAL app.current_tenant = '{tenant}'")
                    )
                result = await session.execute(text(sql), params or {})
                return result.scalar_one()

    spans_of_a = "SELECT count(*) FROM spans WHERE agent_id = :a"
    audits_of_a = f"SELECT count(*) FROM audit_logs WHERE tenant_id = '{tenant_a}'"
    agents_of_a = "SELECT count(*) FROM agents WHERE agent_id = :a"

    # Tenant A sees its own rows; tenant B and no-tenant see none of them
    assert await count_as(tenant_a, spans_of_a, {"a": agent_id}) == 1
    assert await count_as(tenant_b, spans_of_a, {"a": agent_id}) == 0
    assert await count_as(None, spans_of_a, {"a": agent_id}) == 0
    assert await count_as(tenant_a, audits_of_a) == 1
    assert await count_as(tenant_b, audits_of_a) == 0
    assert await count_as(tenant_a, agents_of_a, {"a": agent_id}) == 1
    assert await count_as(tenant_b, agents_of_a, {"a": agent_id}) == 0

    # Agent credential lookup: invisible without the flag, visible with it
    assert await count_as(None, agents_of_a, {"a": agent_id}) == 0
    async with app_sessions() as session:
        async with session.begin():
            await session.execute(text("SET LOCAL app.agent_auth_lookup = 'on'"))
            result = await session.execute(text(agents_of_a), {"a": agent_id})
            assert result.scalar_one() == 1

    await app_engine.dispose()


@pytest.mark.asyncio
async def test_api_flow_against_real_db():
    # NOTE: this flow uses httpx + ASGITransport in this test's single event
    # loop rather than TestClient. The app engine pools asyncpg connections,
    # and TestClient's per-request loops make pooled connections blow up
    # with "attached to a different loop" — a test-harness artifact, not an
    # app bug (a real server runs one loop for the process lifetime).
    from unittest.mock import AsyncMock, patch

    import httpx

    from auth import get_password_hash
    from main import app

    suffix = uuid.uuid4().hex[:8]
    email = f"flow-{suffix}@t.dev"
    password = "SuperSecret1!"

    engine = make_admin_engine()
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO users (email, hashed_password, role) "
                "VALUES (:e, :h, 'admin')"
            ),
            {"e": email, "h": get_password_hash(password)},
        )
    await engine.dispose()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Login. NOTE: the session cookies are Secure, and httpx will not
        # send Secure cookies over plain http://test — so the dashboard
        # calls below use the Bearer token from the login body (the other
        # auth path get_current_user supports; the cookie+CSRF path is
        # covered against the mocked DB in test_integration.py).
        login = await client.post(
            "/v1/auth/token", data={"username": email, "password": password}
        )
        assert login.status_code == 200, login.text
        auth = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create an agent — also writes an audit_logs row via the admin router
        created = await client.post(
            "/v1/admin/agents",
            json={"agent_id": f"flow-agent-{suffix}", "name": "Flow Agent"},
            headers=auth,
        )
        assert created.status_code == 200, created.text
        api_key = created.json()["api_key"]
        agent_id = created.json()["agent_id"]

        # Dashboard summary for this tenant, before any proxied call
        summary = await client.get("/v1/telemetry/summary", headers=auth)
        assert summary.status_code == 200, summary.text

    # Proxied chat completion with the upstream mocked out. A separate
    # client with no browser cookies, like a real agent process.
    fake_payload = {"choices": [{"message": {"content": "hello"}}], "usage": {}}
    fake_response = AsyncMock()
    fake_response.status_code = 200
    fake_response.text = json.dumps(fake_payload)
    fake_response.json = lambda: fake_payload

    with patch("routers.proxy._post_openai_request", return_value=fake_response), patch(
        "routers.proxy.is_agent_suspended", new=AsyncMock(return_value=False)
    ), patch("routers.proxy.check_cost_velocity", new=AsyncMock(return_value=False)):
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as agent_client:
            proxied = await agent_client.post(
                "/v1/chat/completions",
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "hi"}],
                },
                headers={"X-Agent-ID": agent_id, "X-API-Key": api_key},
            )
    assert proxied.status_code == 200, proxied.text
    assert summary.json()["cost"] == 0  # summary was taken before the call

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        summary = await client.get("/v1/telemetry/summary", headers=auth)
        assert summary.status_code == 200, summary.text
        assert summary.json()["cost"] > 0

    # And the span + audit rows really landed, owned by this tenant
    engine = make_admin_engine()
    async with engine.connect() as conn:
        spans = await conn.execute(
            text("SELECT count(*) FROM spans WHERE agent_id = :a"), {"a": agent_id}
        )
        audits = await conn.execute(
            text("SELECT count(*) FROM audit_logs WHERE action = 'agent_created'")
        )
        span_count, audit_count = spans.scalar_one(), audits.scalar_one()
    await engine.dispose()
    assert span_count == 1
    assert audit_count >= 1
