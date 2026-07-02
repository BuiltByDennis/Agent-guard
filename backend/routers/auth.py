from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt
import uuid

from models import User
from database import get_db
from auth import verify_password, create_access_token, get_current_user, create_refresh_token, SECRET_KEY, ALGORITHM
from core.config import settings
from core.limiter import limiter
from core.redis import get_redis
from schemas import TokenResponse

router = APIRouter(prefix="/v1/auth", tags=["auth"])

@router.post("/token")
@limiter.limit("5/minute")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    redis = get_redis()
    lockout_key = f"lockout:{form_data.username}"
    
    if redis:
        attempts = await redis.get(lockout_key)
        if attempts and int(attempts) >= 5:
            raise HTTPException(status_code=403, detail="Account locked due to too many failed attempts")
            
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        if redis:
            await redis.incr(lockout_key)
            await redis.expire(lockout_key, 900) # 15 minutes lockout
        raise HTTPException(status_code=401, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    
    if redis:
        await redis.delete(lockout_key)
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email, "role": user.role}
    )
    
    csrf_token = str(uuid.uuid4())
    
    response = JSONResponse(content={"status": "success", "access_token": access_token}) # access_token in json for legacy/swagger compatibility if needed, but cookies are the primary method
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="strict", max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="strict", max_age=7 * 24 * 60 * 60)
    response.set_cookie(key="csrf_token", value=csrf_token, httponly=False, secure=True, samesite="strict")
    return response

@router.post("/refresh")
@limiter.limit("5/minute")
async def refresh_access_token(request: Request, db: AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
        
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        jti = payload.get("jti")
        email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    redis = get_redis()
    if redis:
        is_blocked = await redis.get(f"blocklist:{jti}")
        if is_blocked:
            raise HTTPException(status_code=401, detail="Refresh token revoked")
        await redis.setex(f"blocklist:{jti}", 7 * 24 * 60 * 60, "true")
        
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(
        data={"sub": user.email, "role": user.role}
    )
    
    response = JSONResponse(content={"status": "success"})
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="strict", max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie(key="refresh_token", value=new_refresh_token, httponly=True, secure=True, samesite="strict", max_age=7 * 24 * 60 * 60)
    return response

@router.post("/logout")
async def logout(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            if jti:
                redis = get_redis()
                if redis:
                    await redis.setex(f"blocklist:{jti}", 7 * 24 * 60 * 60, "true")
        except Exception:
            pass
            
    response = JSONResponse(content={"status": "success"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    response.delete_cookie("csrf_token")
    return response
