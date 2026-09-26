from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    APP_NAME: str = "AI Hub"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # OpenAI / AI Agent settings
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: Optional[str] = None
    AGENT_MAX_ITERATIONS: int = 5
    AGENT_TEMPERATURE: float = 0.2

    # Database settings
    # Default to SQLite for zero-config local run, supports postgresql+asyncpg://
    DATABASE_URL: str = "sqlite+aiosqlite:///./aihub.db"

    # Redis / Cache settings
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TTL: int = 600  # 10 minutes

    # External Provider Keys (optional overrides)
    OPENWEATHER_API_KEY: Optional[str] = None
    EXCHANGERATE_API_KEY: Optional[str] = None
    COINGECKO_API_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None

    # Security & Auth settings
    REQUIRE_AUTH: bool = False  # Set True to strictly enforce authentication even in development
    APP_CLIENT_SECRET: Optional[str] = None  # Optional shared client secret for v1 app clients
    API_KEYS: List[str] = []

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_CHAT_PER_MINUTE: int = 30
    RATE_LIMIT_TOOLS_PER_MINUTE: int = 60

    # Database connection pool settings (for PostgreSQL)
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = False

    # HTTP Client timeouts & retries
    HTTP_TIMEOUT_SECONDS: float = 10.0
    HTTP_MAX_RETRIES: int = 3

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_auth_enforced(self) -> bool:
        return self.is_production or self.REQUIRE_AUTH


settings = Settings()
