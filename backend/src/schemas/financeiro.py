import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CATEGORIAS_DESPESA = ("insumos", "contas_fixas", "manutencao", "outros")
CategoriaDespesa = Literal["insumos", "contas_fixas", "manutencao", "outros"]


class DespesaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    descricao: str = Field(..., min_length=2, max_length=200)
    categoria: CategoriaDespesa = "outros"
    valor: Decimal = Field(..., gt=Decimal("0.00"), max_digits=10, decimal_places=2)
    data_pagamento: date

    @field_validator("descricao")
    @classmethod
    def validar_descricao(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("A descrição da despesa não pode conter caracteres nulos.")
        descricao_limpa = value.strip()
        if len(descricao_limpa) < 2:
            raise ValueError("A descrição da despesa deve ter pelo menos 2 caracteres.")
        return descricao_limpa


class DespesaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    descricao: str | None = Field(default=None, min_length=2, max_length=200)
    categoria: CategoriaDespesa | None = None
    valor: Decimal | None = Field(default=None, gt=Decimal("0.00"), max_digits=10, decimal_places=2)
    data_pagamento: date | None = None

    @field_validator("descricao")
    @classmethod
    def validar_descricao(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if "\x00" in value:
            raise ValueError("A descrição da despesa não pode conter caracteres nulos.")
        descricao_limpa = value.strip()
        if len(descricao_limpa) < 2:
            raise ValueError("A descrição da despesa deve ter pelo menos 2 caracteres.")
        return descricao_limpa

    @model_validator(mode="after")
    def validar_campos_atualizacao(self) -> "DespesaUpdate":
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualização.")
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"O campo '{field_name}' não pode ser nulo.")
        return self


class DespesaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    restaurante_id: uuid.UUID
    descricao: str
    categoria: str | None
    valor: Decimal
    data_pagamento: date
    criado_em: datetime


class ResumoFinanceiroResponse(BaseModel):
    restaurante_id: uuid.UUID
    data_inicio: date | None
    data_fim: date | None
    total_vendas: Decimal
    total_despesas: Decimal
    saldo: Decimal
    despesas_por_categoria: dict[str, Decimal]
