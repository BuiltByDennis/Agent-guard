-- Enable the pgcrypto extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enum for the status to ensure data integrity
CREATE TYPE telemetry_status AS ENUM ('success', 'failed', 'blocked');

-- Enum for common event types
CREATE TYPE telemetry_event_type AS ENUM ('llm_call', 'tool_use', 'agent_routing', 'final_output', 'custom');

CREATE TABLE IF NOT EXISTS agent_telemetry (
    -- 1. Primary Key using UUID
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 2. Grouping identifiers
    trace_id UUID NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    agent_type VARCHAR(255),
    
    -- 3. Event tracking
    event_type telemetry_event_type NOT NULL,
    
    -- 4. Arbitrary metadata for agnostic framework support
    input_data JSONB DEFAULT '{}'::jsonb,
    output_data JSONB DEFAULT '{}'::jsonb,
    
    -- 5. Precise metrics
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER GENERATED ALWAYS AS (prompt_tokens + completion_tokens) STORED,
    cost_usd NUMERIC(10, 6) DEFAULT 0.000000,
    
    -- 6. Latency
    execution_time_ms NUMERIC(10, 2),
    
    -- 7. Status & Errors
    status telemetry_status NOT NULL,
    error_log TEXT,
    
    -- Audit timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for lightning-fast dashboard queries
CREATE INDEX idx_telemetry_trace_id ON agent_telemetry(trace_id);
CREATE INDEX idx_telemetry_agent_id ON agent_telemetry(agent_id);
CREATE INDEX idx_telemetry_status ON agent_telemetry(status);
CREATE INDEX idx_telemetry_created_at ON agent_telemetry(created_at DESC);

-- GIN indexes for querying inside the JSONB payloads (e.g., searching for a specific tool call or parameter)
CREATE INDEX idx_telemetry_input_data ON agent_telemetry USING GIN (input_data);
CREATE INDEX idx_telemetry_output_data ON agent_telemetry USING GIN (output_data);
