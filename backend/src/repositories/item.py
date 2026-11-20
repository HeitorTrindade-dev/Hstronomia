import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.item import Item
from src.repositories.base import BaseRepository


class ItemRepository(BaseRepository[Item]):
    """Repositório de itens do cardápio com isolamento estrito por restaurante_id."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Item, session)

    async def get_by_id_and_restaurante(
        self,
        item_id: uuid.UUID,
        restaurante_id: uuid.UUID,
    ) -> Item | None:
        stmt = select(Item).where(
            Item.id == item_id,
            Item.restaurante_id == restaurante_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_restaurante(
        self,
        restaurante_id: uuid.UUID,
        *,
        apenas_ativos: bool = True,
        apenas_disponiveis: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Item]:
        stmt = select(Item).where(Item.restaurante_id == restaurante_id)
        if apenas_ativos:
            stmt = stmt.where(Item.ativo.is_(True))
        if apenas_disponiveis:
            stmt = stmt.where(Item.disponivel.is_(True))

        stmt = stmt.order_by(Item.nome.asc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        *,
        restaurante_id: uuid.UUID,
        nome: str,
        descricao: str | None,
        preco: Decimal,
        disponivel: bool = True,
    ) -> Item:
        item = Item(
            restaurante_id=restaurante_id,
            nome=nome.strip(),
            descricao=descricao.strip() if descricao is not None else None,
            preco=preco,
            disponivel=disponivel,
            ativo=True,
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def update(
        self,
        *,
        item_id: uuid.UUID,
        restaurante_id: uuid.UUID,
        nome: str | None = None,
        descricao: str | None = None,
        atualizar_descricao: bool = False,
        preco: Decimal | None = None,
        disponivel: bool | None = None,
    ) -> Item | None:
        item = await self.get_by_id_and_restaurante(item_id, restaurante_id)
        if not item:
            return None

        if nome is not None:
            item.nome = nome.strip()
        if atualizar_descricao:
            item.descricao = descricao.strip() if descricao is not None else None
        if preco is not None:
            item.preco = preco
        if disponivel is not None:
            item.disponivel = disponivel

        await self.session.flush()
        return item
