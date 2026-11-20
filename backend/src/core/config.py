from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Banco de Dados PostgreSQL
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "hstronomia"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hstronomia"

    # Autenticação e Segurança (JWT)
    SECRET_KEY: str = "sua-chave-secreta-de-pelo-menos-32-caracteres-para-desenvolvimento"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    OPERATIONAL_TOKEN_EXPIRE_MINUTES: int = 120

    # Rate Limiting (Autenticação Operacional por PIN)
    OPERATIONAL_RATE_LIMIT_MAX_ATTEMPTS: int = 5
    OPERATIONAL_RATE_LIMIT_WINDOW_SECONDS: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
