import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

MAX_BCRYPT_PASSWORD_BYTES = 72


def _validar_senha_bcrypt(value: str) -> str:
    if "\x00" in value:
        raise ValueError("A senha não pode conter caracteres nulos.")
    if len(value.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES:
        raise ValueError("A senha não pode exceder 72 bytes.")
    return value


class DonoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(..., min_length=6, max_length=72)

    @field_validator("nome")
    @classmethod
    def normalizar_nome(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("O nome não pode conter caracteres nulos.")
        limpo = value.strip()
        if len(limpo) < 2:
            raise ValueError("O nome deve ter pelo menos 2 caracteres.")
        return limpo

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, value: str) -> str:
        return _validar_senha_bcrypt(value)


class DonoResponse(BaseModel):
    id: uuid.UUID
    nome: str
    email: EmailStr
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    senha: str = Field(..., min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, value: str) -> str:
        return _validar_senha_bcrypt(value)


class OperacionalLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(..., min_length=1, max_length=100)
    pin: str = Field(..., min_length=4, max_length=20)

    @field_validator("slug")
    @classmethod
    def normalizar_slug(cls, value: str) -> str:
        normalizado = value.strip().lower()
        if not normalizado:
            raise ValueError("Slug do restaurante é obrigatório.")
        return normalizado

    @field_validator("pin")
    @classmethod
    def validar_pin_numerico(cls, value: str) -> str:
        pin_limpo = value.strip()
        if not pin_limpo.isdigit() or not (4 <= len(pin_limpo) <= 20):
            raise ValueError("O PIN deve conter entre 4 e 20 dígitos numéricos.")
        return pin_limpo


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    dono: DonoResponse | None = None
    restaurante_id: uuid.UUID | None = None
    restaurante_nome: str | None = None
    restaurante_slug: str | None = None


class AuthMeResponse(BaseModel):
    role: str  # "dono", "garcom" ou "cozinha"
    dono: DonoResponse | None = None
    restaurante_id: uuid.UUID | None = None
    restaurante_nome: str | None = None
    restaurante_slug: str | None = None
