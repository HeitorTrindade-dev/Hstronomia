from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DEV_SECRET_KEY = "sua-chave-secreta-de-pelo-menos-32-caracteres-para-desenvolvimento"


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_TIMEZONE: str = "UTC"

    # Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Banco de Dados PostgreSQL
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "hstronomia"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hstronomia"

    # Autenticação e Segurança (JWT e Bcrypt)
    SECRET_KEY: str = DEFAULT_DEV_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    OPERATIONAL_TOKEN_EXPIRE_MINUTES: int = 120
    BCRYPT_ROUNDS: int = Field(default=12, ge=4, le=31)

    # Rate Limiting (Autenticação Operacional por PIN e Login do Dono)
    OPERATIONAL_RATE_LIMIT_MAX_ATTEMPTS: int = 5
    OPERATIONAL_RATE_LIMIT_WINDOW_SECONDS: int = 300
    OPERATIONAL_RATE_LIMIT_MAX_KEYS: int = Field(default=10000, ge=100)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("APP_TIMEZONE")
    @classmethod
    def validar_app_timezone(cls, value: str) -> str:
        tz_name = value.strip()
        try:
            ZoneInfo(tz_name)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"Timezone inválido em APP_TIMEZONE: '{value}'.") from exc
        return tz_name

    @model_validator(mode="after")
    def validar_seguranca_producao(self) -> "Settings":
        if self.ENVIRONMENT.strip().lower() == "production":
            chave = self.SECRET_KEY.strip()
            if len(chave) < 32 or chave == DEFAULT_DEV_SECRET_KEY:
                raise ValueError(
                    "Em produção (ENVIRONMENT=production), SECRET_KEY deve ter no mínimo "
                    "32 caracteres e não pode usar o valor padrão de desenvolvimento."
                )
            if self.DEBUG:
                raise ValueError(
                    "Em produção (ENVIRONMENT=production), DEBUG deve ser False."
                )
            if self.BCRYPT_ROUNDS < 12:
                raise ValueError(
                    "Em produção (ENVIRONMENT=production), BCRYPT_ROUNDS deve ser no mínimo 12."
                )
        return self


settings = Settings()
