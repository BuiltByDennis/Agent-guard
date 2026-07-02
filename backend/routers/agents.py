from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, case
from fastapi_cache.decorator import cache

from models import User, InteractionSpan
from auth import get_db_with_rls
from auth import require_admin, get_current_user
from services.velocity import is_agent_suspended
from core.limiter import limiter

router = APIRouter(prefix="/v1/agents", tags=["agents"])

@router.get("/{agent_id}/performance")
@cache(expire=60)
async def get_agent_performance(agent_id: str, db: AsyncSession = Depends(get_db_with_rls), current_user: User = Depends(require_admin)):
    """
    Calculates a dynamic Performance Score for a specific agent by querying the agent_telemetry table.
    Formula: (Success Rate * 0.4) + (Budget Efficiency * 0.3) + (Format Accuracy * 0.3)
    """
    query = select(
        func.count().label("total_rows"),
        func.sum(case((text("status = 'success'"), 1), else_=0)).label("success_rows"),
        func.sum(text("cost_usd")).label("total_cost"),
        func.sum(case((text("status != 'blocked' AND error_log IS NULL"), 1), else_=0)).label("format_accurate_rows")
    ).select_from(text("agent_telemetry")).where(text("agent_id = :agent_id"))
    
    result = await db.execute(query, {"agent_id": agent_id})
    row = result.fetchone()
    
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
    
    success_rate = success_rows / total_rows
    format_accuracy = format_accurate_rows / total_rows
    
    EXPECTED_BASELINE_COST = 0.02
    if total_cost > 0:
        budget_efficiency = (EXPECTED_BASELINE_COST * total_rows) / total_cost
    else:
        budget_efficiency = 1.0
        
    budget_efficiency = min(budget_efficiency, 1.0)
    
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

@router.get("/metrics")
async def get_agents_metrics(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_with_rls),
    current_user: User = Depends(get_current_user)
):
    query = select(
        InteractionSpan.agent_id.label("id"),
        func.max(InteractionSpan.agent_type).label("type"),
        func.avg(InteractionSpan.latency_ms).label("latency"),
        func.sum(InteractionSpan.cost).label("cost")
    ).group_by(InteractionSpan.agent_id).offset(skip).limit(limit)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    agents_metrics = []
    for row in rows:
        is_suspended = await is_agent_suspended(row.id)
        status = "Blocked" if is_suspended else "Emerald"
        agents_metrics.append({
            "id": row.id,
            "type": row.type or "unknown",
            "status": status,
            "latency": round(row.latency or 0),
            "cost": round(row.cost or 0, 4)
        })
    return agents_metrics

@router.get("/{agent_id}/logs")
async def get_agent_logs(
    agent_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: str = Query(None, description="Filter by status_code (e.g., '200' or '403')"),
    db: AsyncSession = Depends(get_db_with_rls),
    current_user: User = Depends(get_current_user)
):
    query = select(InteractionSpan).where(InteractionSpan.agent_id == agent_id)
    
    if status_filter:
        query = query.where(InteractionSpan.status_code == int(status_filter))
        
    query = query.order_by(InteractionSpan.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    spans = result.scalars().all()
    
    return spans
