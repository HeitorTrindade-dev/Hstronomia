import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.comanda import Comanda
from src.models.item_comanda import ItemComanda
from src.repositories.base import TenantBaseRepository


class ItemComandaRepository(TenantBaseRepository[ItemComanda]):
    """Repositório de itens de comanda com isolamento multi-tenant via Comanda.restaurante_id."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ItemComanda, session)

    async def get_by_id_and_restaurante(
        self,
        item_comanda_id: uuid.UUID,
        restaurante_id: uuid.UUID,
        *,
        carregar_comanda: bool = False,
    ) -> ItemComanda | None:
        stmt = (
            select(ItemComanda)
            .join(Comanda, ItemComanda.comanda_id == Comanda.id)
            .where(
                ItemComanda.id == item_comanda_id,
                Comanda.restaurante_id == restaurante_id,
            )
        )
        if carregar_comanda:
            stmt = stmt.options(selectinload(ItemComanda.comanda))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_comanda(
        self,
        comanda_id: uuid.UUID,
        restaurante_id: uuid.UUID,
    ) -> list[ItemComanda]:
        stmt = (
            select(ItemComanda)
            .join(Comanda, ItemComanda.comanda_id == Comanda.id)
            .where(
                ItemComanda.comanda_id == comanda_id,
                Comanda.restaurante_id == restaurante_id,
            )
            .order_by(ItemComanda.criado_em.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_por_status_cozinha(
        self,
        restaurante_id: uuid.UUID,
        *,
        statuses: tuple[str, ...] = ("pendente", "em_preparo"),
        limit: int = 100,
        offset: int = 0,
    ) -> list[ItemComanda]:
        """Lista pedidos de comandas abertas do restaurante filtrados por status para o KDS."""
        stmt = (
            select(ItemComanda)
            .join(Comanda, ItemComanda.comanda_id == Comanda.id)
            .options(selectinload(ItemComanda.comanda))
            .where(
                Comanda.restaurante_id == restaurante_id,
                Comanda.status == "aberta",
                ItemComanda.status.in_(statuses),
            )
            .order_by(ItemComanda.criado_em.asc(), ItemComanda.id.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        *,
        comanda_id: uuid.UUID,
        restaurante_id: uuid.UUID,
        item_id: uuid.UUID,
        nome_item: str,
        quantidade: int,
        preco_unitario: Decimal,
        observacao: str | None = None,
    ) -> ItemComanda | None:
        """Insere item congelado na comanda após validar que ela pertence ao restaurante."""
        stmt = select(Comanda.id).where(
            Comanda.id == comanda_id,
            Comanda.restaurante_id == restaurante_id,
        )
        comanda_valida = (await self.session.execute(stmt)).scalar_one_or_none()
        if not comanda_valida:
            return None

        item_comanda = ItemComanda(
            comanda_id=comanda_id,
            item_id=item_id,
            nome_item=nome_item.strip(),
            quantidade=quantidade,
            preco_unitario=preco_unitario,
            observacao=observacao.strip() if observacao is not None else None,
            status="pendente",
        )
        self.session.add(item_comanda)
        await self.session.flush()
        return item_comanda

    async def update_status(
        self,
        *,
        item_comanda_id: uuid.UUID,
        restaurante_id: uuid.UUID,
        status: str,
        carregar_comanda: bool = False,
    ) -> ItemComanda | None:
        item_comanda = await self.get_by_id_and_restaurante(
            item_comanda_id,
            restaurante_id,
            carregar_comanda=carregar_comanda,
        )
        if not item_comanda:
            return None

        item_comanda.status = status
        await self.session.flush()
        return item_comanda

    async def update_item(
        self,
        *,
        item_comanda_id: uuid.UUID,
        restaurante_id: uuid.UUID,
        quantidade: int | None = None,
        observacao: str | None = None,
        atualizar_observacao: bool = False,
    ) -> ItemComanda | None:
        """Atualiza quantidade/observação preservando nome_item e preco_unitario congelados."""
        item_comanda = await self.get_by_id_and_restaurante(item_comanda_id, restaurante_id)
        if not item_comanda:
            return None

        if quantidade is not None:
            item_comanda.quantidade = quantidade
        if atualizar_observacao:
            item_comanda.observacao = observacao.strip() if observacao is not None else None

        await self.session.flush()
        return item_comanda

    async def delete_by_id_and_restaurante(
        self,
        *,
        item_comanda_id: uuid.UUID,
        restaurante_id: uuid.UUID,
    ) -> bool:
        """Remove um item de comanda após validar que ele pertence ao restaurante."""
        item_comanda = await self.get_by_id_and_restaurante(
            item_comanda_id,
            restaurante_id,
        )
        if not item_comanda:
            return False

        await self.session.delete(item_comanda)
        await self.session.flush()
        return True
