from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    FRONTEND_URL: str = Field(default="http://localhost:3000")
    REDIS_URL: str = Field(default="redis://localhost:6379")
    DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:password@localhost/postgres")
    SENTRY_DSN: str = Field(default="")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1)
    SENTRY_PROFILES_SAMPLE_RATE: float = Field(default=0.1)
    FIREWALL_MODE: str = Field(default="SANITIZE", pattern="^(SANITIZE|BLOCK)$")
    VELOCITY_LIMIT: float = Field(default=5.0)
    VELOCITY_WINDOW_SEC: float = Field(default=60.0)
    OPENAI_API_KEY: str = Field(default="dummy_key")
    SECRET_KEY: str = Field(default="change-me-in-production", alias="JWT_SECRET_KEY")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
