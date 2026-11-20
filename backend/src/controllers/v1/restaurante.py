import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.deps import get_current_dono
from src.core.database import get_db
from src.models.dono import Dono
from src.schemas.restaurante import (
    RestauranteCreate,
    RestaurantePinsUpdate,
    RestaurantePublicoResponse,
    RestauranteResponse,
)
from src.services.restaurante import RestauranteService

router = APIRouter(prefix="/restaurantes", tags=["Restaurantes"])


@router.post(
    "",
    response_model=RestauranteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo restaurante para o Dono autenticado",
)
async def criar_restaurante(
    data: RestauranteCreate,
    current_dono: Annotated[Dono, Depends(get_current_dono)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = RestauranteService(session)
    restaurante = await service.criar_restaurante(dono_id=current_dono.id, data=data)
    await session.commit()
    return restaurante


@router.get(
    "",
    response_model=list[RestauranteResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar restaurantes pertencentes ao Dono autenticado",
)
async def listar_restaurantes_dono(
    current_dono: Annotated[Dono, Depends(get_current_dono)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = RestauranteService(session)
    return await service.listar_por_dono(dono_id=current_dono.id)


@router.get(
    "/slug/{slug}",
    response_model=RestaurantePublicoResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar dados públicos de um restaurante pelo slug (sem expor PINs)",
)
async def obter_restaurante_por_slug(
    slug: str,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = RestauranteService(session)
    return await service.obter_por_slug_publico(slug=slug)


@router.patch(
    "/{restaurante_id}/pins",
    response_model=RestauranteResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotacionar PINs operacionais de Garçom e/ou Cozinha (somente Dono)",
)
async def atualizar_pins_restaurante(
    restaurante_id: uuid.UUID,
    data: RestaurantePinsUpdate,
    current_dono: Annotated[Dono, Depends(get_current_dono)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = RestauranteService(session)
    restaurante = await service.atualizar_pins(
        dono_id=current_dono.id,
        restaurante_id=restaurante_id,
        data=data,
    )
    await session.commit()
    return restaurante
