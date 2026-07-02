from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, case
from datetime import datetime, timedelta

from models import InteractionSpan, User
from auth import get_db_with_rls
from auth import get_current_user

router = APIRouter(prefix="/v1/telemetry", tags=["telemetry"])

@router.get("/time-series")
async def get_telemetry_time_series(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db_with_rls),
    current_user: User = Depends(get_current_user)
):
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = select(
        func.date_trunc('day', InteractionSpan.created_at).label("date"),
        func.sum(InteractionSpan.cost).label("daily_cost"),
        func.avg(InteractionSpan.latency_ms).label("avg_latency")
    ).where(InteractionSpan.created_at >= start_date) \
     .group_by(func.date_trunc('day', InteractionSpan.created_at)) \
     .order_by(func.date_trunc('day', InteractionSpan.created_at))
     
    result = await db.execute(query)
    rows = result.fetchall()
    
    # Format data for recharts
    data = []
    for row in rows:
        data.append({
            "date": row.date.strftime("%Y-%m-%d") if row.date else None,
            "cost": float(row.daily_cost or 0),
            "latency": float(row.avg_latency or 0)
        })
        
    return data

@router.get("/summary")
async def get_telemetry_summary(
    db: AsyncSession = Depends(get_db_with_rls),
    current_user: User = Depends(get_current_user)
):
    query = select(
        func.sum(InteractionSpan.tokens_used).label("total_tokens"),
        func.sum(InteractionSpan.cost).label("total_cost"),
        func.avg(InteractionSpan.latency_ms).label("avg_latency"),
        func.count().label("total_rows"),
        func.sum(case((InteractionSpan.status_code == 200, 1), else_=0)).label("success_rows")
    )
    
    result = await db.execute(query)
    row = result.fetchone()
    
    total_tokens = int(row.total_tokens or 0)
    total_cost = float(row.total_cost or 0.0)
    avg_latency = float(row.avg_latency or 0.0)
    total_rows = int(row.total_rows or 0)
    success_rows = int(row.success_rows or 0)
    
    success_rate = (success_rows / total_rows) if total_rows > 0 else 1.0
    
    return {
        "tokens": total_tokens,
        "cost": total_cost,
        "latency": avg_latency,
        "success_rate": success_rate
    }
