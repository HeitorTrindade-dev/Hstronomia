import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.deps import (
    UserSession,
    get_current_operacional,
    get_dono_restaurante_id,
    get_sessao_restaurante_id,
)
from src.core.database import get_db
from src.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from src.services.item import ItemService

router = APIRouter(prefix="/itens", tags=["Cardápio"])


@router.get(
    "",
    response_model=list[ItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar itens do cardápio do restaurante",
)
async def listar_itens(
    current_user: Annotated[UserSession, Depends(get_current_operacional)],
    restaurante_id: Annotated[uuid.UUID, Depends(get_sessao_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
    incluir_inativos: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    service = ItemService(session)
    pode_ver_inativos = incluir_inativos and current_user.role == "dono"
    return await service.listar_itens(
        restaurante_id=restaurante_id,
        incluir_inativos=pode_ver_inativos,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo item no cardápio (somente Dono)",
)
async def criar_item(
    data: ItemCreate,
    restaurante_id: Annotated[uuid.UUID, Depends(get_dono_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = ItemService(session)
    item = await service.criar_item(restaurante_id=restaurante_id, data=data)
    await session.commit()
    return item


@router.put(
    "/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar dados e preço de um item do cardápio (somente Dono)",
)
async def atualizar_item(
    item_id: uuid.UUID,
    data: ItemUpdate,
    restaurante_id: Annotated[uuid.UUID, Depends(get_dono_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = ItemService(session)
    item = await service.atualizar_item(
        restaurante_id=restaurante_id,
        item_id=item_id,
        data=data,
    )
    await session.commit()
    return item
