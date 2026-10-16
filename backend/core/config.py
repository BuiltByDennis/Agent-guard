from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator

DEFAULT_SECRET_KEY = "change-me-in-production"


class Settings(BaseSettings):
    APP_ENV: str = Field(default="production")
    FRONTEND_URL: str = Field(default="http://localhost:3000")
    REDIS_URL: str = Field(default="redis://localhost:6379")
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost/postgres"
    )
    SENTRY_DSN: str = Field(default="")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1)
    SENTRY_PROFILES_SAMPLE_RATE: float = Field(default=0.1)
    FIREWALL_MODE: str = Field(default="SANITIZE", pattern="^(SANITIZE|BLOCK)$")
    VELOCITY_LIMIT: float = Field(default=5.0)
    VELOCITY_WINDOW_SEC: float = Field(default=60.0)
    OPENAI_API_KEY: str = Field(default="dummy_key")
    SECRET_KEY: str = Field(default=DEFAULT_SECRET_KEY, alias="JWT_SECRET_KEY")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @model_validator(mode="after")
    def _enforce_real_secret_outside_dev(self):
        if (
            self.APP_ENV not in ("development", "test")
            and self.SECRET_KEY == DEFAULT_SECRET_KEY
        ):
            raise ValueError(
                "JWT_SECRET_KEY is still set to the default placeholder. "
                "Set a real secret (openssl rand -hex 32), or set APP_ENV=development/test for local work."
            )
        return self


settings = Settings()
