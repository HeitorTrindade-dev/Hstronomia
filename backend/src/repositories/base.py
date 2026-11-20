import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Repositório base genérico com operações fundamentais de consulta e persistência."""

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, id: uuid.UUID) -> ModelType | None:
        return await self.get_by(self.model.id, id)

    async def get_by(self, field: str | Any, value: Any) -> ModelType | None:
        """Busca um único registro filtrando por qualquer coluna/atributo."""
        column = getattr(self.model, field) if isinstance(field, str) else field
        stmt = select(self.model).where(column == value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by(self, field: str | Any, value: Any) -> list[ModelType]:
        """Lista múltiplos registros filtrando por qualquer coluna/atributo."""
        column = getattr(self.model, field) if isinstance(field, str) else field
        stmt = select(self.model).where(column == value)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[ModelType]:
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_id(self, id: uuid.UUID) -> bool:
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0


class TenantIsolationError(PermissionError, NotImplementedError):
    """Exceção lançada ao tentar executar operação sem escopo de restaurante_id em entidade multi-tenant."""


class TenantBaseRepository(BaseRepository[ModelType]):
    """Repositório base blindado para entidades operacionais multi-tenant (exige restaurante_id)."""

    def _bloquear_acesso_sem_tenant(self, metodo: str) -> None:
        raise TenantIsolationError(
            f"Operação '{self.__class__.__name__}.{metodo}' bloqueada: "
            "entidades operacionais exigem filtragem explícita por restaurante_id (proteção IDOR)."
        )

    async def get_by_id(self, id: uuid.UUID) -> ModelType | None:
        self._bloquear_acesso_sem_tenant("get_by_id")

    async def get_by(self, field: str | Any, value: Any) -> ModelType | None:
        self._bloquear_acesso_sem_tenant("get_by")

    async def list_by(self, field: str | Any, value: Any) -> list[ModelType]:
        self._bloquear_acesso_sem_tenant("list_by")

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[ModelType]:
        self._bloquear_acesso_sem_tenant("list_all")

    async def delete_by_id(self, id: uuid.UUID) -> bool:
        self._bloquear_acesso_sem_tenant("delete_by_id")
