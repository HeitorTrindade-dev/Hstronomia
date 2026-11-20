import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.comanda import Comanda
from src.repositories.base import TenantBaseRepository


class ComandaRepository(TenantBaseRepository[Comanda]):
    """Repositório de comandas com isolamento estrito por restaurante_id."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Comanda, session)

    async def get_by_id_and_restaurante(
        self,
        comanda_id: uuid.UUID,
        restaurante_id: uuid.UUID,
        *,
        carregar_itens: bool = False,
    ) -> Comanda | None:
        stmt = select(Comanda).where(
            Comanda.id == comanda_id,
            Comanda.restaurante_id == restaurante_id,
        )
        if carregar_itens:
            stmt = stmt.options(selectinload(Comanda.itens))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_aberta_por_mesa(
        self,
        restaurante_id: uuid.UUID,
        numero_mesa: int,
    ) -> Comanda | None:
        """Busca comanda aberta vinculada a um número de mesa específico do restaurante."""
        stmt = select(Comanda).where(
            Comanda.restaurante_id == restaurante_id,
            Comanda.numero_mesa == numero_mesa,
            Comanda.status == "aberta",
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_abertas(
        self,
        restaurante_id: uuid.UUID,
        *,
        tipo_atendimento: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Comanda]:
        """Lista comandas abertas do restaurante, com filtro opcional por tipo ('mesa', 'balcao', 'viagem')."""
        return await self.list_by_restaurante(
            restaurante_id=restaurante_id,
            status="aberta",
            tipo_atendimento=tipo_atendimento,
            limit=limit,
            offset=offset,
        )

    async def list_by_restaurante(
        self,
        restaurante_id: uuid.UUID,
        *,
        status: str | None = None,
        tipo_atendimento: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Comanda]:
        stmt = select(Comanda).where(Comanda.restaurante_id == restaurante_id)
        if status is not None:
            stmt = stmt.where(Comanda.status == status)
        if tipo_atendimento is not None:
            stmt = stmt.where(Comanda.tipo_atendimento == tipo_atendimento)

        stmt = stmt.order_by(Comanda.criado_em.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        *,
        restaurante_id: uuid.UUID,
        numero_mesa: int | None = None,
        identificador: str | None = None,
        tipo_atendimento: str = "mesa",
    ) -> Comanda:
        comanda = Comanda(
            restaurante_id=restaurante_id,
            numero_mesa=numero_mesa,
            identificador=identificador.strip() if identificador is not None else None,
            tipo_atendimento=tipo_atendimento,
            status="aberta",
            subtotal=Decimal("0.00"),
            taxa_servico=Decimal("0.00"),
            desconto=Decimal("0.00"),
            valor_total=Decimal("0.00"),
        )
        self.session.add(comanda)
        await self.session.flush()
        return comanda

    async def update_totais(
        self,
        *,
        comanda_id: uuid.UUID,
        restaurante_id: uuid.UUID,
        subtotal: Decimal,
        taxa_servico: Decimal | None = None,
        desconto: Decimal | None = None,
        valor_total: Decimal | None = None,
    ) -> Comanda | None:
        comanda = await self.get_by_id_and_restaurante(comanda_id, restaurante_id)
        if not comanda:
            return None

        comanda.subtotal = subtotal
        if taxa_servico is not None:
            comanda.taxa_servico = taxa_servico
        if desconto is not None:
            comanda.desconto = desconto
        if valor_total is not None:
            comanda.valor_total = valor_total

        await self.session.flush()
        return comanda

    async def fechar(
        self,
        *,
        comanda_id: uuid.UUID,
        restaurante_id: uuid.UUID,
        subtotal: Decimal,
        taxa_servico: Decimal,
        desconto: Decimal,
        valor_total: Decimal,
        metodo_pagamento: str,
        fechado_em: datetime,
    ) -> Comanda | None:
        comanda = await self.get_by_id_and_restaurante(comanda_id, restaurante_id)
        if not comanda:
            return None

        comanda.subtotal = subtotal
        comanda.taxa_servico = taxa_servico
        comanda.desconto = desconto
        comanda.valor_total = valor_total
        comanda.metodo_pagamento = metodo_pagamento
        comanda.status = "fechada"
        comanda.fechado_em = fechado_em

        await self.session.flush()
        return comanda

    async def cancelar(
        self,
        *,
        comanda_id: uuid.UUID,
        restaurante_id: uuid.UUID,
        fechado_em: datetime,
    ) -> Comanda | None:
        comanda = await self.get_by_id_and_restaurante(comanda_id, restaurante_id)
        if not comanda:
            return None

        comanda.status = "cancelada"
        comanda.fechado_em = fechado_em

        await self.session.flush()
        return comanda

    async def somar_vendas_fechadas_periodo(
        self,
        restaurante_id: uuid.UUID,
        *,
        inicio: datetime | None = None,
        fim: datetime | None = None,
    ) -> Decimal:
        """Consolida o faturamento de comandas fechadas do restaurante no período."""
        stmt = select(func.coalesce(func.sum(Comanda.valor_total), Decimal("0.00"))).where(
            Comanda.restaurante_id == restaurante_id,
            Comanda.status == "fechada",
        )
        if inicio is not None:
            stmt = stmt.where(Comanda.fechado_em >= inicio)
        if fim is not None:
            stmt = stmt.where(Comanda.fechado_em <= fim)

        result = await self.session.execute(stmt)
        total = result.scalar_one()
        return Decimal(total)
