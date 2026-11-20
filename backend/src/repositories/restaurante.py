import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.restaurante import Restaurante


class RestauranteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, restaurante_id: uuid.UUID) -> Optional[Restaurante]:
        stmt = select(Restaurante).where(Restaurante.id == restaurante_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Restaurante]:
        stmt = select(Restaurante).where(Restaurante.slug == slug.strip().lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_dono_id(self, dono_id: uuid.UUID) -> List[Restaurante]:
        stmt = select(Restaurante).where(Restaurante.dono_id == dono_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        dono_id: uuid.UUID,
        nome: str,
        slug: str,
        codigo_garcom: str,
        codigo_cozinha: str,
    ) -> Restaurante:
        restaurante = Restaurante(
            dono_id=dono_id,
            nome=nome.strip(),
            slug=slug.strip().lower(),
            codigo_garcom=codigo_garcom.strip(),
            codigo_cozinha=codigo_cozinha.strip(),
        )
        self.session.add(restaurante)
        await self.session.flush()
        return restaurante

    async def update_pins(
        self,
        restaurante_id: uuid.UUID,
        dono_id: uuid.UUID,
        codigo_garcom: Optional[str] = None,
        codigo_cozinha: Optional[str] = None,
    ) -> Optional[Restaurante]:
        # Validação estrita de IDOR: dono_id + restaurante_id
        restaurante = await self.get_by_id(restaurante_id)
        if not restaurante or restaurante.dono_id != dono_id:
            return None

        if codigo_garcom is not None:
            restaurante.codigo_garcom = codigo_garcom.strip()
        if codigo_cozinha is not None:
            restaurante.codigo_cozinha = codigo_cozinha.strip()

        await self.session.flush()
        return restaurante
