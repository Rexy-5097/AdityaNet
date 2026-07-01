from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "SuryaNet"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS Configurations
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # TimescaleDB / PostgreSQL Configurations
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres_secure_pass"
    POSTGRES_DB: str = "suryanet"

    DATABASE_ASYNC_URL: str = "postgresql+asyncpg://postgres:postgres_secure_pass@localhost:5432/suryanet"
    DATABASE_SYNC_URL: str = "postgresql://postgres:postgres_secure_pass@localhost:5432/suryanet"

    # Redis Configurations
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://localhost:6379/0"


settings = Settings()
