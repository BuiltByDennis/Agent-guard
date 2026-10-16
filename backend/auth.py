import jwt
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, Request
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from typing import Optional

from models import User, Agent
from database import get_db, AsyncSessionLocal
from core.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Password hashing: pwdlib with Argon2 (default) + Bcrypt (legacy support).
# The default-secret guard lives in core.config.Settings and fails fast.

# Initialize with both Argon2 (new default) and Bcrypt (legacy support)
password_hash = PasswordHash(
    (
        Argon2Hasher(),
        BcryptHasher(),
    )
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/token")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "type": "refresh", "jti": jti})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def verify_agent_api_key(
    request: Request,
    api_key: str = Depends(api_key_header),
    db: AsyncSession = Depends(get_db),
):
    agent_id = request.headers.get("X-Agent-ID")
    if not agent_id:
        raise HTTPException(status_code=400, detail="Missing X-Agent-ID header")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    # The agents table is RLS-forced, and the tenant is not known until the
    # agent is found. The Phase 1 policy lets this one lookup through when
    # the session raises the agent-auth flag (SET LOCAL = this transaction).
    await db.execute(text("SET LOCAL app.agent_auth_lookup = 'on'"))
    result = await db.execute(
        select(Agent).where(Agent.agent_id == agent_id, Agent.deleted_at.is_(None))
    )
    agent = result.scalar_one_or_none()

    if (
        not agent
        or not verify_password(api_key, agent.hashed_api_key)
        or not agent.is_active
    ):
        raise HTTPException(status_code=401, detail="Invalid API Key or inactive agent")

    return agent


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        if email is None or token_type != "access":
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return current_user


async def get_db_with_rls(current_user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        # Inject the user's ID into the Postgres session for RLS.
        # SET LOCAL does not support parameter placeholders in asyncpg, so emit a literal value.
        tenant_id = str(current_user.id).replace("'", "''")
        await session.execute(text(f"SET LOCAL app.current_tenant = '{tenant_id}'"))
        yield session
