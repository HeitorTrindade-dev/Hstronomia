import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.deps import get_atendimento_restaurante_id
from src.core.database import get_db
from src.schemas.comanda import (
    ComandaCreate,
    ComandaDetalheResponse,
    ComandaFecharRequest,
    ComandaPreviaResponse,
    ComandaResponse,
    ItemComandaCreate,
    ItemComandaResponse,
    StatusComanda,
    TipoAtendimento,
)
from src.services.comanda import ComandaService

router = APIRouter(prefix="/comandas", tags=["Comandas"])


@router.get(
    "",
    response_model=list[ComandaResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar comandas do restaurante com filtros opcionais (Garçom ou Dono)",
)
async def listar_comandas(
    restaurante_id: Annotated[uuid.UUID, Depends(get_atendimento_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
    status_comanda: Annotated[StatusComanda | None, Query(alias="status")] = None,
    tipo_atendimento: Annotated[TipoAtendimento | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    service = ComandaService(session)
    return await service.listar_comandas(
        restaurante_id=restaurante_id,
        status_filtro=status_comanda,
        tipo_atendimento=tipo_atendimento,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{comanda_id}",
    response_model=ComandaDetalheResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter detalhes de uma comanda e seus itens congelados (Garçom ou Dono)",
)
async def obter_comanda(
    comanda_id: uuid.UUID,
    restaurante_id: Annotated[uuid.UUID, Depends(get_atendimento_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = ComandaService(session)
    return await service.obter_comanda(
        restaurante_id=restaurante_id,
        comanda_id=comanda_id,
    )


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


@router.get(
    "/{comanda_id}/previa",
    response_model=ComandaPreviaResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter prévia financeira da comanda com 10% opcional e desconto (Garçom ou Dono)",
)
async def obter_previa_comanda(
    comanda_id: uuid.UUID,
    restaurante_id: Annotated[uuid.UUID, Depends(get_atendimento_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
    incluir_taxa_servico: Annotated[bool, Query()] = True,
    desconto: Annotated[
        Decimal,
        Query(ge=Decimal("0.00"), max_digits=10, decimal_places=2),
    ] = Decimal("0.00"),
):
    service = ComandaService(session)
    return await service.obter_previa(
        restaurante_id=restaurante_id,
        comanda_id=comanda_id,
        incluir_taxa_servico=incluir_taxa_servico,
        desconto=desconto,
    )


@router.post(
    "/{comanda_id}/fechar",
    response_model=ComandaResponse,
    status_code=status.HTTP_200_OK,
    summary="Fechar comanda calculando subtotal, taxa de serviço, desconto e valor total (Garçom ou Dono)",
)
async def fechar_comanda(
    comanda_id: uuid.UUID,
    data: ComandaFecharRequest,
    restaurante_id: Annotated[uuid.UUID, Depends(get_atendimento_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = ComandaService(session)
    comanda = await service.fechar_comanda(
        restaurante_id=restaurante_id,
        comanda_id=comanda_id,
        data=data,
    )
    await session.commit()
    return comanda


@router.post(
    "/{comanda_id}/cancelar",
    response_model=ComandaResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancelar uma comanda aberta e liberar a mesa (Garçom ou Dono)",
)
async def cancelar_comanda(
    comanda_id: uuid.UUID,
    restaurante_id: Annotated[uuid.UUID, Depends(get_atendimento_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = ComandaService(session)
    comanda = await service.cancelar_comanda(
        restaurante_id=restaurante_id,
        comanda_id=comanda_id,
    )
    await session.commit()
    return comanda
