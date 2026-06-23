import os
import time
import json
import logging
import re
import asyncio
from typing import Dict
from collections import deque
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, text
from datetime import timedelta

from models import Base, InteractionSpan, AgentTelemetry, User, Agent
from database import AsyncSessionLocal, get_db
from auth import verify_agent_api_key, verify_password, create_access_token, require_admin, ACCESS_TOKEN_EXPIRE_MINUTES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent Proxy")

# Firewall config
FIREWALL_MODE = os.getenv("FIREWALL_MODE", "SANITIZE") # SANITIZE or BLOCK

# 1. Manual Kill Switch Status (True = Suspended)
AGENT_STATUS: Dict[str, bool] = {
    "suspended-agent": True
}

# 2. Cost Velocity Tracker (Sliding Window)
# Format: { agent_id: deque([(timestamp, cost), ...]) }
VELOCITY_WINDOWS: Dict[str, deque] = {}
VELOCITY_LOCK = asyncio.Lock()
VELOCITY_LIMIT = 5.0  # $5.00 limit
VELOCITY_WINDOW_SEC = 60.0

# 3. Regex Patterns for Data Leakage
REGEX_SSN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
REGEX_CC = re.compile(r'\b(?:\d[ -]*?){13,16}\b') # Simple PAN approximation
REGEX_API_KEY = re.compile(r'\bsk-[a-zA-Z0-9]{48}\b')

async def init_db():
    pass # Managed by Alembic migrations now

async def save_interaction_to_db(span_data: dict):
    try:
        async with AsyncSessionLocal() as session:
            new_span = InteractionSpan(**span_data)
            session.add(new_span)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to save to database: {e}")

async def check_cost_velocity(agent_id: str, new_cost: float) -> bool:
    """Checks if agent exceeded velocity. Returns True if exceeded."""
    now = time.time()
    async with VELOCITY_LOCK:
        if agent_id not in VELOCITY_WINDOWS:
            VELOCITY_WINDOWS[agent_id] = deque()
        
        window = VELOCITY_WINDOWS[agent_id]
        
        # Prune old entries
        while window and now - window[0][0] > VELOCITY_WINDOW_SEC:
            window.popleft()
            
        # Sum current cost
        current_sum = sum(cost for _, cost in window)
        
        if current_sum + new_cost > VELOCITY_LIMIT:
            return True
            
        # Append new cost
        window.append((now, new_cost))
        return False

def scan_and_redact(text_content: str) -> tuple[str, bool]:
    """Returns (redacted_text, has_violation)"""
    has_violation = False
    
    if REGEX_SSN.search(text_content) or REGEX_CC.search(text_content) or REGEX_API_KEY.search(text_content):
        has_violation = True
        
    if has_violation and FIREWALL_MODE == "SANITIZE":
        text_content = REGEX_SSN.sub('[REDACTED_BY_FIREWALL]', text_content)
        text_content = REGEX_CC.sub('[REDACTED_BY_FIREWALL]', text_content)
        text_content = REGEX_API_KEY.sub('[REDACTED_BY_FIREWALL]', text_content)
        
    return text_content, has_violation

async def stream_openai_response(request_json: dict, background_tasks: BackgroundTasks, agent_id: str, agent_type: str, start_time: float):
    openai_api_key = os.getenv("OPENAI_API_KEY", "dummy_key")
    url = "https://api.openai.com/v1/chat/completions"
    forward_headers = {"Authorization": f"Bearer {openai_api_key}", "Content-Type": "application/json"}
    client = httpx.AsyncClient()
    req = client.build_request("POST", url, json=request_json, headers=forward_headers)
    response = await client.send(req, stream=True)
    
    async def stream_generator():
        token_count = 0
        status_code = response.status_code
        buffer = ""
        violation_blocked = False
        
        try:
            async for chunk in response.aiter_text():
                token_count += len(chunk.encode()) // 4  
                buffer += chunk
                
                # Check buffer for newline or if it gets large
                if '\n' in buffer or len(buffer) > 100:
                    redacted, has_violation = scan_and_redact(buffer)
                    if has_violation and FIREWALL_MODE == "BLOCK":
                        violation_blocked = True
                        yield b'{"error": "Compliance violation detected. Stream blocked by Firewall."}'
                        break
                    
                    yield redacted.encode('utf-8')
                    buffer = ""
            
            # Flush remaining buffer
            if buffer and not violation_blocked:
                redacted, has_violation = scan_and_redact(buffer)
                if has_violation and FIREWALL_MODE == "BLOCK":
                    violation_blocked = True
                    yield b'{"error": "Compliance violation detected. Stream blocked by Firewall."}'
                else:
                    yield redacted.encode('utf-8')
        finally:
            latency_ms = (time.time() - start_time) * 1000
            cost = (token_count / 1000) * 0.002
            
            span_data = {
                "agent_id": agent_id,
                "agent_type": agent_type,
                "latency_ms": latency_ms,
                "tokens_used": token_count,
                "cost": cost,
                "status_code": 403 if violation_blocked else status_code,
                "payload": request_json
            }
            
            if violation_blocked:
                span_data["error_log"] = "Post-Flight Firewall: Data leakage blocked."
            
            # Check velocity post-flight for stream since we only know cost now
            if not violation_blocked:
                is_exceeded = await check_cost_velocity(agent_id, cost)
                if is_exceeded:
                    AGENT_STATUS[agent_id] = True
                    span_data["error_log"] = "Automated Kill Switch: Cost velocity limit breached mid-stream."
            
            background_tasks.add_task(save_interaction_to_db, span_data)
            await response.aclose()
            await client.aclose()
    
    return StreamingResponse(stream_generator(), status_code=response.status_code, media_type=response.headers.get("content-type"))

@app.post("/v1/auth/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/v1/chat/completions")
async def chat_completions(request: Request, background_tasks: BackgroundTasks, agent: Agent = Depends(verify_agent_api_key)):
    start_time = time.time()
    
    agent_id = agent.agent_id
    agent_type = request.headers.get("X-Agent-Type", "general")
    
    # 1. Pre-Flight Manual Kill Switch
    if AGENT_STATUS.get(agent_id) is True:
        raise HTTPException(status_code=403, detail={"error": "Agent execution halted: Manual kill-switch activated."})
        
    # 2. Pre-Flight Cost Velocity Guardrail (Automated Kill Switch)
    # Fast check of the current sum before any cost is added
    async with VELOCITY_LOCK:
        if agent_id in VELOCITY_WINDOWS:
            now = time.time()
            window = VELOCITY_WINDOWS[agent_id]
            while window and now - window[0][0] > VELOCITY_WINDOW_SEC:
                window.popleft()
            current_sum = sum(cost for _, cost in window)
            if current_sum > VELOCITY_LIMIT:
                AGENT_STATUS[agent_id] = True
                # Log blocked telemetry
                span_data = {
                    "agent_id": agent_id, "agent_type": agent_type, "latency_ms": 0,
                    "tokens_used": 0, "cost": 0, "status_code": 402,
                    "payload": {}, "error_log": "Automated Kill Switch: Cost velocity limit breached."
                }
                background_tasks.add_task(save_interaction_to_db, span_data)
                raise HTTPException(status_code=402, detail="Payment Required: Cost velocity limit breached.")

    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    is_stream = body.get("stream", False)
    
    if is_stream:
        return await stream_openai_response(body, background_tasks, agent_id, agent_type, start_time)
    else:
        openai_api_key = os.getenv("OPENAI_API_KEY", "dummy_key")
        url = "https://api.openai.com/v1/chat/completions"
        forward_headers = {"Authorization": f"Bearer {openai_api_key}", "Content-Type": "application/json"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=body, headers=forward_headers)
            
            token_count = len(response.text) // 4
            latency_ms = (time.time() - start_time) * 1000
            cost = (token_count / 1000) * 0.002
            
            # Post-Flight Firewall Scan
            response_text = response.text
            redacted, has_violation = scan_and_redact(response_text)
            
            if has_violation and FIREWALL_MODE == "BLOCK":
                span_data = {
                    "agent_id": agent_id, "agent_type": agent_type, "latency_ms": latency_ms,
                    "tokens_used": token_count, "cost": cost, "status_code": 403,
                    "payload": body, "error_log": "Post-Flight Firewall: Data leakage blocked."
                }
                background_tasks.add_task(save_interaction_to_db, span_data)
                raise HTTPException(status_code=403, detail="Compliance violation detected. Response blocked by Firewall.")
                
            # Update Velocity
            is_exceeded = await check_cost_velocity(agent_id, cost)
            error_log = None
            if is_exceeded:
                AGENT_STATUS[agent_id] = True
                error_log = "Automated Kill Switch: Cost velocity limit breached post-flight."

            span_data = {
                "agent_id": agent_id, "agent_type": agent_type, "latency_ms": latency_ms,
                "tokens_used": token_count, "cost": cost, "status_code": response.status_code,
                "payload": body, "error_log": error_log
            }
            background_tasks.add_task(save_interaction_to_db, span_data)
            
            if has_violation and FIREWALL_MODE == "SANITIZE":
                try:
                    return json.loads(redacted)
                except:
                    return StreamingResponse(iter([redacted.encode()]))
            return response.json()

@app.get("/v1/agents/{agent_id}/performance")
async def get_agent_performance(agent_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    """
    Calculates a dynamic Performance Score for a specific agent by querying the agent_telemetry table.
    Formula: (Success Rate * 0.4) + (Budget Efficiency * 0.3) + (Format Accuracy * 0.3)
    """
    # Build the query using conditional aggregation for efficiency
    query = select(
        func.count().label("total_rows"),
        func.sum(case((text("status = 'success'"), 1), else_=0)).label("success_rows"),
        func.sum(text("cost_usd")).label("total_cost"),
        func.sum(case((text("status != 'blocked' AND error_log IS NULL"), 1), else_=0)).label("format_accurate_rows")
    ).select_from(text("agent_telemetry")).where(text("agent_id = :agent_id"))
    
    result = await db.execute(query, {"agent_id": agent_id})
    row = result.fetchone()
    
    # Edge case: 0 total records
    if not row or row.total_rows == 0:
        return {
            "overall_score": 100,
            "breakdown": {
                "success_rate": 1.0,
                "budget_efficiency": 1.0,
                "format_accuracy": 1.0
            }
        }
        
    total_rows = row.total_rows
    success_rows = row.success_rows or 0
    total_cost = float(row.total_cost or 0.0)
    format_accurate_rows = row.format_accurate_rows or 0
    
    # 1. Success Rate (40%)
    success_rate = success_rows / total_rows
    
    # 2. Format Accuracy (30%)
    format_accuracy = format_accurate_rows / total_rows
    
    # 3. Budget Efficiency (30%)
    EXPECTED_BASELINE_COST = 0.02
    if total_cost > 0:
        budget_efficiency = (EXPECTED_BASELINE_COST * total_rows) / total_cost
    else:
        budget_efficiency = 1.0
        
    # Cap budget efficiency at 1.0 maximum
    budget_efficiency = min(budget_efficiency, 1.0)
    
    # Final Score Calculation
    performance_score = (success_rate * 0.4) + (budget_efficiency * 0.3) + (format_accuracy * 0.3)
    
    return {
        "overall_score": round(performance_score * 100),
        "breakdown": {
            "success_rate": round(success_rate, 4),
            "budget_efficiency": round(budget_efficiency, 4),
            "format_accuracy": round(format_accuracy, 4),
            "raw_metrics": {
                "total_rows": total_rows,
                "success_rows": success_rows,
                "total_cost": total_cost,
                "format_accurate_rows": format_accurate_rows
            }
        }
    }
