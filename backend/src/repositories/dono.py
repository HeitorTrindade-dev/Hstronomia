
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.dono import Dono
from src.repositories.base import BaseRepository


class DonoRepository(BaseRepository[Dono]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Dono, session)

    async def get_by_email(self, email: str) -> Dono | None:
        return await self.get_by(Dono.email, email.strip().lower())

    async def create(self, nome: str, email: str, senha_hash: str) -> Dono:
        dono = Dono(
            nome=nome.strip(),
            email=email.strip().lower(),
            senha_hash=senha_hash,
        )
        self.session.add(dono)
        await self.session.flush()
        return dono
