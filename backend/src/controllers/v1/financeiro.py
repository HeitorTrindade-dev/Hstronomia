import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.deps import get_dono_restaurante_id
from src.core.database import get_db
from src.schemas.financeiro import (
    CategoriaDespesa,
    DespesaCreate,
    DespesaResponse,
    DespesaUpdate,
    ResumoFinanceiroResponse,
)
from src.services.financeiro import FinanceiroService

router = APIRouter(prefix="/financeiro", tags=["Financeiro"])


@router.post(
    "/despesas",
    response_model=DespesaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar nova despesa operacional (somente Dono)",
)
async def criar_despesa(
    data: DespesaCreate,
    restaurante_id: Annotated[uuid.UUID, Depends(get_dono_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = FinanceiroService(session)
    despesa = await service.criar_despesa(restaurante_id=restaurante_id, data=data)
    await session.commit()
    return despesa


@router.get(
    "/despesas",
    response_model=list[DespesaResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar despesas do restaurante com filtros por período e categoria (somente Dono)",
)
async def listar_despesas(
    restaurante_id: Annotated[uuid.UUID, Depends(get_dono_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
    data_inicio: Annotated[date | None, Query()] = None,
    data_fim: Annotated[date | None, Query()] = None,
    categoria: Annotated[CategoriaDespesa | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    service = FinanceiroService(session)
    return await service.listar_despesas(
        restaurante_id=restaurante_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        categoria=categoria,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/despesas/{despesa_id}",
    response_model=DespesaResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter detalhes de uma despesa específica (somente Dono)",
)
async def obter_despesa(
    despesa_id: uuid.UUID,
    restaurante_id: Annotated[uuid.UUID, Depends(get_dono_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = FinanceiroService(session)
    return await service.obter_despesa(restaurante_id=restaurante_id, despesa_id=despesa_id)


@router.patch(
    "/despesas/{despesa_id}",
    response_model=DespesaResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar parcialmente uma despesa (somente Dono)",
)
async def atualizar_despesa(
    despesa_id: uuid.UUID,
    data: DespesaUpdate,
    restaurante_id: Annotated[uuid.UUID, Depends(get_dono_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = FinanceiroService(session)
    despesa = await service.atualizar_despesa(
        restaurante_id=restaurante_id,
        despesa_id=despesa_id,
        data=data,
    )
    await session.commit()
    return despesa


@router.delete(
    "/despesas/{despesa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Excluir uma despesa (somente Dono)",
)
async def excluir_despesa(
    despesa_id: uuid.UUID,
    restaurante_id: Annotated[uuid.UUID, Depends(get_dono_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = FinanceiroService(session)
    await service.excluir_despesa(restaurante_id=restaurante_id, despesa_id=despesa_id)
    await session.commit()


@router.get(
    "/resumo",
    response_model=ResumoFinanceiroResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter resumo financeiro consolidado de vendas vs despesas (somente Dono)",
)
async def obter_resumo_financeiro(
    restaurante_id: Annotated[uuid.UUID, Depends(get_dono_restaurante_id)],
    session: Annotated[AsyncSession, Depends(get_db)],
    data_inicio: Annotated[date | None, Query()] = None,
    data_fim: Annotated[date | None, Query()] = None,
):
    service = FinanceiroService(session)
    return await service.obter_resumo(
        restaurante_id=restaurante_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )
