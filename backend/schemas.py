from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Dict, Any

class ChatCompletionRequest(BaseModel):
    model: str = Field(default="gpt-4", description="The model to use for completion.")
    messages: list[Dict[str, Any]] = Field(description="List of messages in the conversation.")
    stream: bool = Field(default=False, description="Whether to stream the response.")
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class AgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    agent_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$", description="Alphanumeric with dashes or underscores only.")

class AgentStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|suspended)$", description="The new status of the agent.")

class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long and contain at least one uppercase, lowercase, number, and special character.")
    role: str = Field(default="viewer", pattern="^(admin|viewer)$")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        import re
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", v):
            raise ValueError("Password must be at least 8 characters long and contain at least one uppercase, lowercase, number, and special character.")
        return v

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
