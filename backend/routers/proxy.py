import httpx
import time
import json
import tiktoken
from fastapi import APIRouter, Request, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from models import Agent
from auth import verify_agent_api_key
from core.config import settings
from core.dependencies import get_agent_id
from core.http_client import get_http_client
from services.firewall import scan_and_redact
from services.velocity import check_cost_velocity, is_agent_suspended, suspend_agent
from services.telemetry import save_interaction_to_db
from schemas import ChatCompletionRequest
from core.limiter import limiter

router = APIRouter(prefix="/v1", tags=["proxy"])

@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
)
async def _send_openai_request(client: httpx.AsyncClient, req: httpx.Request, stream: bool = False):
    response = await client.send(req, stream=stream)
    if response.status_code >= 500 or response.status_code == 429:
        response.raise_for_status()
    return response

@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
)
async def _post_openai_request(client: httpx.AsyncClient, url: str, **kwargs):
    response = await client.post(url, **kwargs)
    if response.status_code >= 500 or response.status_code == 429:
        response.raise_for_status()
    return response

def num_tokens_from_string(string: str, model_name: str) -> int:
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(string))

async def stream_openai_response(request_json: dict, background_tasks: BackgroundTasks, agent: Agent, agent_type: str, start_time: float, model: str):
    agent_id = agent.agent_id
    tenant_id = str(agent.tenant_id)
    url = "https://api.openai.com/v1/chat/completions"
    forward_headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}
    
    http_client = get_http_client()
    req = http_client.build_request("POST", url, json=request_json, headers=forward_headers)
    response = await _send_openai_request(http_client, req, stream=True)
    
    async def stream_generator():
        token_count = 0
        status_code = response.status_code
        buffer = ""
        violation_blocked = False
        full_text = ""
        
        try:
            async for chunk in response.aiter_text():
                buffer += chunk
                
                if '\n' in buffer or len(buffer) > 100:
                    redacted, has_violation = scan_and_redact(buffer)
                    if has_violation and settings.FIREWALL_MODE == "BLOCK":
                        violation_blocked = True
                        yield b'{"error": "Compliance violation detected. Stream blocked by Firewall."}'
                        break
                    
                    yield redacted.encode('utf-8')
                    full_text += redacted
                    buffer = ""
            
            if buffer and not violation_blocked:
                redacted, has_violation = scan_and_redact(buffer)
                if has_violation and settings.FIREWALL_MODE == "BLOCK":
                    violation_blocked = True
                    yield b'{"error": "Compliance violation detected. Stream blocked by Firewall."}'
                else:
                    yield redacted.encode('utf-8')
                    full_text += redacted
        finally:
            token_count = num_tokens_from_string(full_text, model)
            latency_ms = (time.time() - start_time) * 1000
            cost = (token_count / 1000) * 0.002
            
            span_data = {
                "tenant_id": tenant_id,
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
            
            if not violation_blocked:
                is_exceeded = await check_cost_velocity(agent_id, cost)
                if is_exceeded:
                    await suspend_agent(agent_id)
                    span_data["error_log"] = "Automated Kill Switch: Cost velocity limit breached post-flight."
            
            background_tasks.add_task(save_interaction_to_db, span_data)
            await response.aclose()
    
    return StreamingResponse(stream_generator(), status_code=response.status_code, media_type=response.headers.get("content-type"))

@router.post("/chat/completions")
@limiter.limit("100/minute", key_func=get_agent_id)
async def chat_completions(request: Request, body: ChatCompletionRequest, background_tasks: BackgroundTasks, agent: Agent = Depends(verify_agent_api_key)):
    start_time = time.time()
    
    agent_id = agent.agent_id
    agent_type = request.headers.get("X-Agent-Type", "general")
    
    if await is_agent_suspended(agent_id):
        raise HTTPException(status_code=403, detail="Agent is suspended.")
        
    if settings.REDIS_URL:
        # Cost check logic
        pass

    is_stream = body.stream
    
    if is_stream:
        return await stream_openai_response(body.model_dump(), background_tasks, agent, agent_type, start_time, body.model)
    else:
        url = "https://api.openai.com/v1/chat/completions"
        forward_headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}
        
        http_client = get_http_client()
        response = await _post_openai_request(http_client, url, json=body.model_dump(), headers=forward_headers)
        
        token_count = num_tokens_from_string(response.text, body.model)
        latency_ms = (time.time() - start_time) * 1000
        cost = (token_count / 1000) * 0.002
        
        response_text = response.text
        redacted, has_violation = scan_and_redact(response_text)
        
        if has_violation and settings.FIREWALL_MODE == "BLOCK":
            span_data = {
                "tenant_id": str(agent.tenant_id),
                "agent_id": agent_id, "agent_type": agent_type, "latency_ms": latency_ms,
                "tokens_used": token_count, "cost": cost, "status_code": 403,
                "payload": body.model_dump(), "error_log": "Post-Flight Firewall: Data leakage blocked."
            }
            background_tasks.add_task(save_interaction_to_db, span_data)
            raise HTTPException(status_code=403, detail="Compliance violation detected. Response blocked by Firewall.")
            
        error_log = None
        is_exceeded = await check_cost_velocity(agent_id, cost)
        if is_exceeded:
            await suspend_agent(agent_id)
            error_log = "Automated Kill Switch: Cost velocity limit breached post-flight."

        span_data = {
            "tenant_id": str(agent.tenant_id),
            "agent_id": agent_id, "agent_type": agent_type, "latency_ms": latency_ms,
            "tokens_used": token_count, "cost": cost, "status_code": response.status_code,
            "payload": body.model_dump(), "error_log": error_log
        }
        background_tasks.add_task(save_interaction_to_db, span_data)
        
        if has_violation and settings.FIREWALL_MODE == "SANITIZE":
            try:
                return json.loads(redacted)
            except Exception:
                return StreamingResponse(iter([redacted.encode()]))
        return response.json()
