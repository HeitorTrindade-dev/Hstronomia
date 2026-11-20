import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.deps import get_cozinha_restaurante_id
from src.core.database import get_db
from src.schemas.cozinha import (
    CozinhaPedidoResponse,
    CozinhaPedidoStatusUpdate,
    StatusFilaCozinha,
)
from src.services.cozinha import CozinhaService

router = APIRouter(prefix="/cozinha", tags=["Cozinha (KDS)"])


@router.get(
    "/pedidos",
    response_model=list[CozinhaPedidoResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar fila KDS de pedidos pendentes ou em preparo",
)
async def listar_pedidos_cozinha(
    restaurante_id: Annotated[uuid.UUID, Depends(get_cozinha_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
    status_pedido: Annotated[StatusFilaCozinha | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    service = CozinhaService(session)
    return await service.listar_pedidos(
        restaurante_id=restaurante_id,
        status_filtro=status_pedido,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/pedidos/{item_comanda_id}/status",
    response_model=CozinhaPedidoResponse,
    status_code=status.HTTP_200_OK,
    summary="Avançar status de um pedido na cozinha (pendente -> em_preparo -> pronto -> entregue)",
)
async def atualizar_status_pedido_cozinha(
    item_comanda_id: uuid.UUID,
    data: CozinhaPedidoStatusUpdate,
    restaurante_id: Annotated[uuid.UUID, Depends(get_cozinha_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = CozinhaService(session)
    pedido = await service.atualizar_status_pedido(
        restaurante_id=restaurante_id,
        item_comanda_id=item_comanda_id,
        novo_status=data.status,
    )
    await session.commit()
    return pedido
