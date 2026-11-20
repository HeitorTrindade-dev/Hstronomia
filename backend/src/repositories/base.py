import uuid
from typing import Any, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Repositório base genérico com operações fundamentais de consulta e persistência."""

    def __init__(self, model: Type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        return await self.get_by(self.model.id, id)

    async def get_by(self, field: Union[str, Any], value: Any) -> Optional[ModelType]:
        """Busca um único registro filtrando por qualquer coluna/atributo."""
        column = getattr(self.model, field) if isinstance(field, str) else field
        stmt = select(self.model).where(column == value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by(self, field: Union[str, Any], value: Any) -> List[ModelType]:
        """Lista múltiplos registros filtrando por qualquer coluna/atributo."""
        column = getattr(self.model, field) if isinstance(field, str) else field
        stmt = select(self.model).where(column == value)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_id(self, id: uuid.UUID) -> bool:
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
