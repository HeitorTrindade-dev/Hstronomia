import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class DonoCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(..., min_length=6, max_length=100)


class DonoResponse(BaseModel):
    id: uuid.UUID
    nome: str
    email: EmailStr
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(..., min_length=1)


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
    dono: Optional[DonoResponse] = None
    restaurante_id: Optional[uuid.UUID] = None
    restaurante_nome: Optional[str] = None
    restaurante_slug: Optional[str] = None


class AuthMeResponse(BaseModel):
    role: str  # "dono", "garcom" ou "cozinha"
    dono: Optional[DonoResponse] = None
    restaurante_id: Optional[uuid.UUID] = None
    restaurante_nome: Optional[str] = None
    restaurante_slug: Optional[str] = None
