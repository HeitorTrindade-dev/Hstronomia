import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.restaurante import Restaurante
from src.repositories.base import BaseRepository, TenantIsolationError


class RestauranteRepository(BaseRepository[Restaurante]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Restaurante, session)

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Restaurante]:
        raise TenantIsolationError(
            "Operação 'RestauranteRepository.list_all' bloqueada: "
            "utilize get_by_dono_id(dono_id=...) para isolamento por proprietário."
        )

    async def delete_by_id(self, id: uuid.UUID) -> bool:
        raise TenantIsolationError(
            "Operação 'RestauranteRepository.delete_by_id' bloqueada: "
            "exclusão sem validação explícita de dono_id é proibida."
        )

    async def get_by_slug(self, slug: str) -> Restaurante | None:
        return await self.get_by(Restaurante.slug, slug.strip().lower())

    async def get_by_dono_id(self, dono_id: uuid.UUID) -> list[Restaurante]:
        return await self.list_by(Restaurante.dono_id, dono_id)

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
        codigo_garcom: str | None = None,
        codigo_cozinha: str | None = None,
    ) -> Restaurante | None:
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

    async def update_dados(
        self,
        *,
        restaurante_id: uuid.UUID,
        dono_id: uuid.UUID,
        nome: str | None = None,
        slug: str | None = None,
    ) -> Restaurante | None:
        restaurante = await self.get_by_id(restaurante_id)
        if not restaurante or restaurante.dono_id != dono_id:
            return None

        if nome is not None:
            restaurante.nome = nome.strip()
        if slug is not None:
            restaurante.slug = slug.strip().lower()

        await self.session.flush()
        return restaurante
