from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
import secrets
from datetime import datetime

from models import User, Agent, AuditLog
from auth import get_db_with_rls
from auth import require_admin, get_password_hash
from schemas import AgentCreateRequest, AgentStatusUpdate, UserCreateRequest
from services.velocity import suspend_agent, unsuspend_agent

router = APIRouter(prefix="/v1/admin", tags=["admin"])

async def log_admin_action(db: AsyncSession, tenant_id: str, performed_by: str, action: str, resource_id: str = None, details: dict = None):
    audit_log = AuditLog(
        tenant_id=tenant_id,
        performed_by=performed_by,
        action=action,
        resource_id=resource_id,
        details=details
    )
    db.add(audit_log)

@router.patch("/agents/{agent_id}/status")
async def update_agent_status(agent_id: str, status_data: AgentStatusUpdate, db: AsyncSession = Depends(get_db_with_rls), current_user: User = Depends(require_admin)):
    if status_data.status == "suspended":
        await suspend_agent(agent_id)
    elif status_data.status == "active":
        await unsuspend_agent(agent_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    await log_admin_action(db, current_user.id, current_user.id, f"agent_{status_data.status}", agent_id)
    await db.commit()
    
    return {"message": f"Agent {agent_id} status updated to {status_data.status}"}

@router.post("/agents")
async def create_agent(agent_data: AgentCreateRequest, db: AsyncSession = Depends(get_db_with_rls), current_user: User = Depends(require_admin)):
    api_key = f"sk-{secrets.token_urlsafe(32)}"
    hashed_key = get_password_hash(api_key)
    
    new_agent = Agent(
        tenant_id=current_user.id,
        agent_id=agent_data.agent_id,
        name=agent_data.name,
        hashed_api_key=hashed_key,
        is_active=True,
        created_by=current_user.id
    )
    db.add(new_agent)
    
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agent ID already exists.")
        
    await log_admin_action(db, current_user.id, current_user.id, "agent_created", agent_data.agent_id)
    await db.commit()
    
    return {"message": "Agent created", "api_key": api_key, "agent_id": agent_data.agent_id}

@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db_with_rls), current_user: User = Depends(require_admin)):
    result = await db.execute(select(Agent).where(Agent.agent_id == agent_id, Agent.tenant_id == current_user.id))
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    agent.deleted_at = datetime.utcnow()
    await log_admin_action(db, current_user.id, current_user.id, "agent_deleted", agent_id)
    await db.commit()
    
    return {"message": f"Agent {agent_id} soft deleted"}

@router.post("/users")
async def create_user(user_data: UserCreateRequest, db: AsyncSession = Depends(get_db_with_rls), current_user: User = Depends(require_admin)):
    hashed_pwd = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pwd,
        role=user_data.role
    )
    db.add(new_user)
    
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User email already exists.")
        
    await log_admin_action(db, current_user.id, current_user.id, "user_created", user_data.email)
    await db.commit()
    
    return {"message": "User created", "email": user_data.email}

@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db_with_rls), current_user: User = Depends(require_admin)):
    result = await db.execute(select(User).where(User.deleted_at.is_(None)))
    users = result.scalars().all()
    return [{"id": str(u.id), "email": u.email, "role": u.role, "created_at": u.updated_at} for u in users]

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db_with_rls), current_user: User = Depends(require_admin)):
    result = await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.deleted_at = datetime.utcnow()
    await log_admin_action(db, current_user.id, current_user.id, "user_deleted", user_id)
    await db.commit()
    
    return {"message": f"User {user_id} revoked"}
