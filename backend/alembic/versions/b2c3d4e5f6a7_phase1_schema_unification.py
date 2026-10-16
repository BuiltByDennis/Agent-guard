"""Phase 1: schema unification — audit_logs, missing columns, RLS

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-16

Before this revision the codebase had three conflicting schema sources
(models.py, the initial migration, and the loose schema.sql /
enable_rls.sql files, both deleted in Phase 1). Databases in the wild may
therefore be in the initial-migration shape or in a create_all shape.
Every change below is guarded, so the migration converges either shape —
and is safe to re-run.

What it does:
- users:  + updated_at, deleted_at (present in the model, missing in DB)
- agents: + created_by, updated_at, deleted_at
- audit_logs: created (the model and admin router used it; no migration
  had ever created it, so every admin action failed on migrated DBs)
- Row-Level Security is enabled and FORCEd on the tenant-scoped tables
  (agents, spans, agent_telemetry, audit_logs) with policies that compare
  tenant_id as text — comparing via a ::uuid cast raises an error whenever
  the tenant setting is empty, which breaks pre-tenant queries.
- The agents policy additionally honours the ``app.agent_auth_lookup``
  session flag, which the proxy's API-key verification sets: an agent's
  credentials must be lookable-up before its tenant is known.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None

TENANT_TABLES = ("agents", "spans", "agent_telemetry", "audit_logs")


def _columns(table: str) -> set:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _has_policy(table: str, policy: str) -> bool:
    row = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT 1 FROM pg_policies WHERE tablename = :t AND policyname = :p"
            ),
            {"t": table, "p": policy},
        )
        .first()
    )
    return row is not None


def upgrade() -> None:
    # --- users: missing columns -------------------------------------------
    cols = _columns("users")
    if "updated_at" not in cols:
        op.add_column(
            "users",
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.text("current_timestamp"),
                nullable=True,
            ),
        )
    if "deleted_at" not in cols:
        op.add_column(
            "users",
            sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        )

    # --- agents: missing columns ------------------------------------------
    cols = _columns("agents")
    if "created_by" not in cols:
        op.add_column(
            "agents",
            sa.Column(
                "created_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id"),
                nullable=True,
            ),
        )
    if "updated_at" not in cols:
        op.add_column(
            "agents",
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.text("current_timestamp"),
                nullable=True,
            ),
        )
    if "deleted_at" not in cols:
        op.add_column(
            "agents",
            sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        )

    # --- audit_logs: whole table ------------------------------------------
    if not _has_table("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                server_default=sa.text("gen_random_uuid()"),
                nullable=False,
            ),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("performed_by", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("action", sa.String(length=255), nullable=False),
            sa.Column("resource_id", sa.String(length=255), nullable=True),
            sa.Column(
                "details", postgresql.JSONB(astext_type=sa.Text()), nullable=True
            ),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.text("current_timestamp"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["tenant_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["performed_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_audit_logs_tenant_id"), "audit_logs", ["tenant_id"], unique=False
        )
        op.create_index(
            op.f("ix_audit_logs_performed_by"),
            "audit_logs",
            ["performed_by"],
            unique=False,
        )
        op.create_index(
            op.f("ix_audit_logs_created_at"),
            "audit_logs",
            ["created_at"],
            unique=False,
        )

    # --- Row-Level Security -------------------------------------------------
    # Policies compare tenant_id as text: current_setting(..., true)
    # returns '' when unset, and ''::uuid raises — which would turn every
    # pre-tenant query into a 500 instead of an empty result.
    tenant_expr = "tenant_id::text = current_setting('app.current_tenant', true)"
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        policy = f"tenant_isolation_{table}"
        if _has_policy(table, policy):
            continue
        if table == "agents":
            # Agent API-key verification runs before the tenant is known;
            # it sets app.agent_auth_lookup = 'on' for its lookup query.
            using = (
                f"({tenant_expr} OR "
                "current_setting('app.agent_auth_lookup', true) = 'on')"
            )
            op.execute(
                f"CREATE POLICY {policy} ON {table} USING {using} "
                f"WITH CHECK ({tenant_expr})"
            )
        else:
            op.execute(
                f"CREATE POLICY {policy} ON {table} USING ({tenant_expr}) "
                f"WITH CHECK ({tenant_expr})"
            )


def downgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    op.drop_table("audit_logs")

    op.drop_column("agents", "deleted_at")
    op.drop_column("agents", "updated_at")
    op.drop_column("agents", "created_by")

    op.drop_column("users", "deleted_at")
    op.drop_column("users", "updated_at")
