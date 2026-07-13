"""Application configuration via pydantic-settings."""
from functools import lru_cache
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "FutureLens"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://futurelens:futurelens_secret@localhost:5432/futurelens_db"

    # JWT
    SECRET_KEY: str = "change-me-to-a-real-secret-key-at-least-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Monte Carlo
    MONTE_CARLO_SIMULATIONS: int = 10000
    MONTE_CARLO_SEED: int = 42

    # Market Return Assumptions (annualized)
    EQUITY_MEAN_RETURN: float = 0.12
    EQUITY_VOLATILITY: float = 0.18
    DEBT_MEAN_RETURN: float = 0.07
    DEBT_VOLATILITY: float = 0.03
    HYBRID_MEAN_RETURN: float = 0.10
    HYBRID_VOLATILITY: float = 0.12

    # Tax
    EFFECTIVE_TAX_RATE: float = 0.20  # 20% effective tax rate assumption for net income calculation


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
