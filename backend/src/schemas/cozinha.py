import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

StatusItemCozinha = Literal["pendente", "em_preparo", "pronto", "entregue"]
StatusFilaCozinha = Literal["pendente", "em_preparo"]


class CozinhaPedidoStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: StatusItemCozinha


class CozinhaPedidoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    comanda_id: uuid.UUID
    item_id: uuid.UUID
    nome_item: str
    quantidade: int
    observacao: str | None
    status: StatusItemCozinha
    criado_em: datetime
    numero_mesa: int | None
    identificador: str | None
    tipo_atendimento: str
