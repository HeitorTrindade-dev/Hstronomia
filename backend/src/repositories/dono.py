import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.dono import Dono


class DonoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, dono_id: uuid.UUID) -> Optional[Dono]:
        stmt = select(Dono).where(Dono.id == dono_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Dono]:
        stmt = select(Dono).where(Dono.email == email.strip().lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, nome: str, email: str, senha_hash: str) -> Dono:
        dono = Dono(
            nome=nome.strip(),
            email=email.strip().lower(),
            senha_hash=senha_hash,
        )
        self.session.add(dono)
        await self.session.flush()
        return dono
