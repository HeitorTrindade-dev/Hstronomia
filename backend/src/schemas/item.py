import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str = Field(..., min_length=2, max_length=120)
    descricao: str | None = Field(default=None, max_length=1000)
    preco: Decimal = Field(..., gt=Decimal("0.00"), max_digits=10, decimal_places=2)
    disponivel: bool = True

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, value: str) -> str:
        nome_limpo = value.strip()
        if len(nome_limpo) < 2:
            raise ValueError("O nome do item deve ter pelo menos 2 caracteres.")
        return nome_limpo

    @field_validator("descricao")
    @classmethod
    def normalizar_descricao(cls, value: str | None) -> str | None:
        if value is None:
            return None
        limpa = value.strip()
        return limpa or None


class ItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str | None = Field(default=None, min_length=2, max_length=120)
    descricao: str | None = Field(default=None, max_length=1000)
    preco: Decimal | None = Field(default=None, gt=Decimal("0.00"), max_digits=10, decimal_places=2)
    disponivel: bool | None = None

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, value: str | None) -> str | None:
        if value is None:
            return None
        nome_limpo = value.strip()
        if len(nome_limpo) < 2:
            raise ValueError("O nome do item deve ter pelo menos 2 caracteres.")
        return nome_limpo

    @field_validator("descricao")
    @classmethod
    def normalizar_descricao(cls, value: str | None) -> str | None:
        if value is None:
            return None
        limpa = value.strip()
        return limpa or None


class ItemDisponibilidadeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    disponivel: bool


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    restaurante_id: uuid.UUID
    nome: str
    descricao: str | None
    preco: Decimal
    disponivel: bool
    ativo: bool
    criado_em: datetime
