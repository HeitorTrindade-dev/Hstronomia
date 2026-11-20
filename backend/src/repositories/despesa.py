import uuid
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.despesa import Despesa
from src.repositories.base import BaseRepository

CENTAVOS = Decimal("0.01")


class DespesaRepository(BaseRepository[Despesa]):
    """Repositório de despesas com isolamento estrito por restaurante_id."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Despesa, session)

    async def get_by_id_and_restaurante(
        self,
        despesa_id: uuid.UUID,
        restaurante_id: uuid.UUID,
    ) -> Despesa | None:
        stmt = select(Despesa).where(
            Despesa.id == despesa_id,
            Despesa.restaurante_id == restaurante_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_restaurante(
        self,
        restaurante_id: uuid.UUID,
        *,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        categoria: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Despesa]:
        stmt = select(Despesa).where(Despesa.restaurante_id == restaurante_id)
        if data_inicio is not None:
            stmt = stmt.where(Despesa.data_pagamento >= data_inicio)
        if data_fim is not None:
            stmt = stmt.where(Despesa.data_pagamento <= data_fim)
        if categoria is not None:
            stmt = stmt.where(Despesa.categoria == categoria)

        stmt = (
            stmt.order_by(Despesa.data_pagamento.desc(), Despesa.criado_em.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        *,
        restaurante_id: uuid.UUID,
        descricao: str,
        categoria: str | None,
        valor: Decimal,
        data_pagamento: date,
    ) -> Despesa:
        despesa = Despesa(
            restaurante_id=restaurante_id,
            descricao=descricao.strip(),
            categoria=categoria,
            valor=valor,
            data_pagamento=data_pagamento,
        )
        self.session.add(despesa)
        await self.session.flush()
        return despesa

    async def update(
        self,
        *,
        despesa_id: uuid.UUID,
        restaurante_id: uuid.UUID,
        descricao: str | None = None,
        categoria: str | None = None,
        atualizar_categoria: bool = False,
        valor: Decimal | None = None,
        data_pagamento: date | None = None,
    ) -> Despesa | None:
        despesa = await self.get_by_id_and_restaurante(despesa_id, restaurante_id)
        if not despesa:
            return None

        if descricao is not None:
            despesa.descricao = descricao.strip()
        if atualizar_categoria or categoria is not None:
            despesa.categoria = categoria
        if valor is not None:
            despesa.valor = valor
        if data_pagamento is not None:
            despesa.data_pagamento = data_pagamento

        await self.session.flush()
        return despesa

    async def delete_by_id_and_restaurante(
        self,
        *,
        despesa_id: uuid.UUID,
        restaurante_id: uuid.UUID,
    ) -> bool:
        stmt = delete(Despesa).where(
            Despesa.id == despesa_id,
            Despesa.restaurante_id == restaurante_id,
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return (result.rowcount or 0) > 0

    async def somar_despesas_periodo(
        self,
        restaurante_id: uuid.UUID,
        *,
        inicio: date | None = None,
        fim: date | None = None,
    ) -> Decimal:
        """Consolida o total de despesas do restaurante no período."""
        stmt = select(func.coalesce(func.sum(Despesa.valor), Decimal("0.00"))).where(
            Despesa.restaurante_id == restaurante_id,
        )
        if inicio is not None:
            stmt = stmt.where(Despesa.data_pagamento >= inicio)
        if fim is not None:
            stmt = stmt.where(Despesa.data_pagamento <= fim)

        result = await self.session.execute(stmt)
        total = result.scalar_one()
        return Decimal(str(total)).quantize(CENTAVOS, rounding=ROUND_HALF_UP)

    async def somar_despesas_por_categoria(
        self,
        restaurante_id: uuid.UUID,
        *,
        inicio: date | None = None,
        fim: date | None = None,
    ) -> dict[str, Decimal]:
        """Agrupa o total de despesas do restaurante por categoria no período."""
        categoria_col = func.coalesce(Despesa.categoria, "outros")
        stmt = select(
            categoria_col,
            func.coalesce(func.sum(Despesa.valor), Decimal("0.00")),
        ).where(Despesa.restaurante_id == restaurante_id)
        if inicio is not None:
            stmt = stmt.where(Despesa.data_pagamento >= inicio)
        if fim is not None:
            stmt = stmt.where(Despesa.data_pagamento <= fim)

        stmt = stmt.group_by(categoria_col)
        result = await self.session.execute(stmt)
        return {
            str(categoria): Decimal(str(total)).quantize(CENTAVOS, rounding=ROUND_HALF_UP)
            for categoria, total in result.all()
        }
