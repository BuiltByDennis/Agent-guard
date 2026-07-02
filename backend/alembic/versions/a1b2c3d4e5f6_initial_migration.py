"""Initial migration

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2026-06-23 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Users
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='viewer'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Agents
    op.create_table('agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('hashed_api_key', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agents_agent_id'), 'agents', ['agent_id'], unique=True)
    op.create_index(op.f('ix_agents_tenant_id'), 'agents', ['tenant_id'], unique=False)

    # Spans
    op.create_table('spans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('agent_type', sa.String(), nullable=True),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('error_log', sa.String(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('current_timestamp'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_spans_agent_id'), 'spans', ['agent_id'], unique=False)
    op.create_index(op.f('ix_spans_created_at'), 'spans', ['created_at'], unique=False)
    op.create_index(op.f('ix_spans_id'), 'spans', ['id'], unique=False)
    op.create_index(op.f('ix_spans_tenant_id'), 'spans', ['tenant_id'], unique=False)

    # Agent Telemetry
    # We need to create the ENUM types first
    telemetry_event_type = postgresql.ENUM('llm_call', 'tool_use', 'agent_routing', 'final_output', 'custom', name='telemetry_event_type')
    telemetry_event_type.create(op.get_bind())
    
    telemetry_status = postgresql.ENUM('success', 'failed', 'blocked', name='telemetry_status')
    telemetry_status.create(op.get_bind())

    op.create_table('agent_telemetry',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(length=255), nullable=False),
        sa.Column('agent_type', sa.String(length=255), nullable=True),
        sa.Column('event_type', telemetry_event_type, nullable=False),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('total_tokens', sa.Integer(), sa.Computed('prompt_tokens + completion_tokens', persisted=True), nullable=True),
        sa.Column('cost_usd', sa.NUMERIC(precision=10, scale=6), server_default=sa.text('0.000000'), nullable=True),
        sa.Column('execution_time_ms', sa.NUMERIC(precision=10, scale=2), nullable=True),
        sa.Column('status', telemetry_status, nullable=False),
        sa.Column('error_log', sa.String(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('current_timestamp'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_telemetry_agent_id'), 'agent_telemetry', ['agent_id'], unique=False)
    op.create_index(op.f('ix_agent_telemetry_created_at'), 'agent_telemetry', ['created_at'], unique=False)
    op.create_index(op.f('ix_agent_telemetry_status'), 'agent_telemetry', ['status'], unique=False)
    op.create_index(op.f('ix_agent_telemetry_tenant_id'), 'agent_telemetry', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_agent_telemetry_trace_id'), 'agent_telemetry', ['trace_id'], unique=False)

def downgrade() -> None:
    op.drop_table('agent_telemetry')
    op.drop_table('spans')
    op.drop_table('agents')
    op.drop_table('users')
    
    # Drop ENUM types
    postgresql.ENUM(name='telemetry_event_type').drop(op.get_bind())
    postgresql.ENUM(name='telemetry_status').drop(op.get_bind())
