import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.deps import get_atendimento_restaurante_id
from src.core.database import get_db
from src.schemas.comanda import (
    ComandaCreate,
    ComandaResponse,
    ItemComandaCreate,
    ItemComandaResponse,
)
from src.services.comanda import ComandaService

router = APIRouter(prefix="/comandas", tags=["Comandas"])


@router.post(
    "",
    response_model=ComandaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir nova comanda de atendimento (Garçom ou Dono)",
)
async def abrir_comanda(
    data: ComandaCreate,
    restaurante_id: Annotated[uuid.UUID, Depends(get_atendimento_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = ComandaService(session)
    comanda = await service.abrir_comanda(restaurante_id=restaurante_id, data=data)
    await session.commit()
    return comanda


@router.post(
    "/{comanda_id}/itens",
    response_model=ItemComandaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar item à comanda com congelamento de nome e preço (Garçom ou Dono)",
)
async def adicionar_item_comanda(
    comanda_id: uuid.UUID,
    data: ItemComandaCreate,
    restaurante_id: Annotated[uuid.UUID, Depends(get_atendimento_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = ComandaService(session)
    item_comanda = await service.adicionar_item(
        restaurante_id=restaurante_id,
        comanda_id=comanda_id,
        data=data,
    )
    await session.commit()
    return item_comanda
