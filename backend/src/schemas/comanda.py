import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
    model_validator,
)


class ComandaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    numero_mesa: StrictInt | None = Field(default=None, ge=1, le=9999)
    identificador: str | None = Field(default=None, max_length=100)
    tipo_atendimento: Literal["mesa", "balcao", "viagem"] = "mesa"

    @field_validator("identificador")
    @classmethod
    def normalizar_identificador(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if "\x00" in value:
            raise ValueError("O identificador não pode conter caracteres nulos.")
        limpo = value.strip()
        return limpo or None

    @model_validator(mode="after")
    def validar_identificacao_minima(self) -> "ComandaCreate":
        if self.numero_mesa is None and self.identificador is None:
            raise ValueError(
                "Informe o número da mesa ou um identificador para abrir a comanda."
            )
        if self.tipo_atendimento == "mesa" and self.numero_mesa is None:
            raise ValueError(
                "Para atendimento em mesa, o número da mesa é obrigatório."
            )
        if self.tipo_atendimento in ("balcao", "viagem") and self.numero_mesa is not None:
            raise ValueError(
                "Pedidos de balcão ou viagem não devem informar número de mesa."
            )
        return self


class ComandaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    numero_mesa: StrictInt | None = Field(default=None, ge=1, le=9999)
    identificador: str | None = Field(default=None, max_length=100)
    tipo_atendimento: Literal["mesa", "balcao", "viagem"] | None = None

    @field_validator("identificador")
    @classmethod
    def normalizar_identificador(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if "\x00" in value:
            raise ValueError("O identificador não pode conter caracteres nulos.")
        limpo = value.strip()
        return limpo or None

    @model_validator(mode="after")
    def validar_campos_atualizacao(self) -> "ComandaUpdate":
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualização.")
        if "tipo_atendimento" in self.model_fields_set and self.tipo_atendimento is None:
            raise ValueError("O campo 'tipo_atendimento' não pode ser nulo.")
        return self


class ComandaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    restaurante_id: uuid.UUID
    numero_mesa: int | None
    identificador: str | None
    tipo_atendimento: str
    status: str
    subtotal: Decimal
    taxa_servico: Decimal
    desconto: Decimal
    valor_total: Decimal
    metodo_pagamento: str | None
    criado_em: datetime
    fechado_em: datetime | None


class ItemComandaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: uuid.UUID
    quantidade: StrictInt = Field(default=1, ge=1, le=999)
    observacao: str | None = Field(default=None, max_length=500)

    @field_validator("observacao")
    @classmethod
    def normalizar_observacao(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if "\x00" in value:
            raise ValueError("A observação não pode conter caracteres nulos.")
        limpa = value.strip()
        return limpa or None


class ItemComandaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantidade: StrictInt | None = Field(default=None, ge=1, le=999)
    observacao: str | None = Field(default=None, max_length=500)

    @field_validator("observacao")
    @classmethod
    def normalizar_observacao(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if "\x00" in value:
            raise ValueError("A observação não pode conter caracteres nulos.")
        limpa = value.strip()
        return limpa or None

    @model_validator(mode="after")
    def validar_campos_atualizacao(self) -> "ItemComandaUpdate":
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualização.")
        if "quantidade" in self.model_fields_set and self.quantidade is None:
            raise ValueError("O campo 'quantidade' não pode ser nulo.")
        return self


class ItemComandaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    comanda_id: uuid.UUID
    item_id: uuid.UUID
    nome_item: str
    quantidade: int
    preco_unitario: Decimal
    observacao: str | None
    status: str
    criado_em: datetime


MetodoPagamento = Literal["pix", "dinheiro", "cartao_credito", "cartao_debito"]
StatusComanda = Literal["aberta", "fechada", "cancelada"]
TipoAtendimento = Literal["mesa", "balcao", "viagem"]


class ComandaDetalheResponse(ComandaResponse):
    itens: list[ItemComandaResponse]


class ComandaFecharRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metodo_pagamento: MetodoPagamento
    incluir_taxa_servico: bool = True
    desconto: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
    )


class ComandaPreviaResponse(BaseModel):
    comanda_id: uuid.UUID
    restaurante_id: uuid.UUID
    numero_mesa: int | None
    identificador: str | None
    tipo_atendimento: str
    status: str
    itens: list[ItemComandaResponse]
    subtotal: Decimal
    incluir_taxa_servico: bool
    taxa_servico: Decimal
    desconto: Decimal
    valor_total: Decimal
