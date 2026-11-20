import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.restaurante import Restaurante
from src.repositories.restaurante import RestauranteRepository
from src.schemas.restaurante import RestauranteCreate, RestaurantePinsUpdate

logger = logging.getLogger(__name__)


class RestauranteService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.restaurante_repo = RestauranteRepository(session)

    async def criar_restaurante(
        self,
        dono_id: uuid.UUID,
        data: RestauranteCreate,
    ) -> Restaurante:
        existente = await self.restaurante_repo.get_by_slug(data.slug)
        if existente is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um restaurante cadastrado com este slug.",
            )

        try:
            restaurante = await self.restaurante_repo.create(
                dono_id=dono_id,
                nome=data.nome,
                slug=data.slug,
                codigo_garcom=data.codigo_garcom,
                codigo_cozinha=data.codigo_cozinha,
            )
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um restaurante cadastrado com este slug.",
            ) from None

        logger.info(
            "Restaurante criado (dono_id=%s, restaurante_id=%s, slug=%s)",
            dono_id,
            restaurante.id,
            restaurante.slug,
        )
        return restaurante

    async def listar_por_dono(self, dono_id: uuid.UUID) -> list[Restaurante]:
        return await self.restaurante_repo.get_by_dono_id(dono_id)

    async def obter_por_slug_publico(self, slug: str) -> Restaurante:
        slug_normalizado = slug.strip().lower()
        restaurante = await self.restaurante_repo.get_by_slug(slug_normalizado)
        if not restaurante:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurante não encontrado.",
            )
        return restaurante

    async def atualizar_pins(
        self,
        dono_id: uuid.UUID,
        restaurante_id: uuid.UUID,
        data: RestaurantePinsUpdate,
    ) -> Restaurante:
        restaurante = await self.restaurante_repo.get_by_id(restaurante_id)
        if not restaurante or restaurante.dono_id != dono_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurante não encontrado.",
            )

        novo_garcom = (
            data.codigo_garcom
            if data.codigo_garcom is not None
            else restaurante.codigo_garcom
        )
        novo_cozinha = (
            data.codigo_cozinha
            if data.codigo_cozinha is not None
            else restaurante.codigo_cozinha
        )
        if novo_garcom == novo_cozinha:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O PIN do garçom e o PIN da cozinha devem ser diferentes.",
            )

        atualizado = await self.restaurante_repo.update_pins(
            restaurante_id=restaurante_id,
            dono_id=dono_id,
            codigo_garcom=data.codigo_garcom,
            codigo_cozinha=data.codigo_cozinha,
        )
        if not atualizado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurante não encontrado.",
            )

        logger.info(
            "PINs operacionais atualizados (dono_id=%s, restaurante_id=%s)",
            dono_id,
            restaurante_id,
        )
        return atualizado
