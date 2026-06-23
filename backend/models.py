import uuid
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, JSON, text, Computed, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM, NUMERIC, TIMESTAMP
from sqlalchemy.sql import func

Base = declarative_base()

class InteractionSpan(Base):
    __tablename__ = "spans"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, index=True)
    agent_type = Column(String)
    latency_ms = Column(Float)
    tokens_used = Column(Integer)
    cost = Column(Float)
    status_code = Column(Integer)
    payload = Column(JSON)
    error_log = Column(String, nullable=True)

class AgentTelemetry(Base):
    __tablename__ = "agent_telemetry"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    trace_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    agent_id = Column(String(255), nullable=False, index=True)
    agent_type = Column(String(255))
    
    event_type = Column(ENUM('llm_call', 'tool_use', 'agent_routing', 'final_output', 'custom', name='telemetry_event_type', create_type=True), nullable=False)
    
    input_data = Column(JSONB, server_default=text("'{}'::jsonb"))
    output_data = Column(JSONB, server_default=text("'{}'::jsonb"))
    
    prompt_tokens = Column(Integer, server_default=text("0"))
    completion_tokens = Column(Integer, server_default=text("0"))
    total_tokens = Column(Integer, Computed("prompt_tokens + completion_tokens", persisted=True))
    cost_usd = Column(NUMERIC(10, 6), server_default=text("0.000000"))
    
    execution_time_ms = Column(NUMERIC(10, 2))
    
    status = Column(ENUM('success', 'failed', 'blocked', name='telemetry_status', create_type=True), nullable=False, index=True)
    error_log = Column(String)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp(), index=True)

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="viewer", nullable=False)

class Agent(Base):
    __tablename__ = "agents"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    agent_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255))
    hashed_api_key = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
