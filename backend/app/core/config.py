"""
Application Settings — loaded from environment variables.

Uses pydantic-settings for type-safe configuration with validation.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "DebtSense"
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_WORKERS: int = 4

    # Database
    USE_SQLITE: bool = False
    SQLITE_PATH: str = "debtsense_dev.db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "debtsense"
    POSTGRES_USER: str = "debtsense_user"
    POSTGRES_PASSWORD: str = "change_me_in_production"

    @property
    def DATABASE_URL(self) -> str:
        if self.USE_SQLITE:
            return f"sqlite+aiosqlite:///{self.SQLITE_PATH}"
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        if self.USE_SQLITE:
            return f"sqlite:///{self.SQLITE_PATH}"
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # JWT
    JWT_SECRET_KEY: str = "change-this-to-a-random-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # LLM
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4"
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.3
    LLM_FALLBACK_PROVIDER: str = ""
    LLM_FALLBACK_API_KEY: str = ""
    LLM_FALLBACK_MODEL: str = ""

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Encryption
    ENCRYPTION_KEY: str = "change-this-32-byte-key-in-prod!"

    # Sentry
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
