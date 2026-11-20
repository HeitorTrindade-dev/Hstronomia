import logging
import uuid
from datetime import UTC, date, datetime, time
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.despesa import Despesa
from src.repositories.comanda import ComandaRepository
from src.repositories.despesa import DespesaRepository
from src.schemas.financeiro import (
    CATEGORIAS_DESPESA,
    DespesaCreate,
    DespesaUpdate,
    ResumoFinanceiroResponse,
)

logger = logging.getLogger(__name__)
CENTAVOS = Decimal("0.01")


class FinanceiroService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.despesa_repo = DespesaRepository(session)
        self.comanda_repo = ComandaRepository(session)

    @staticmethod
    def _quantizar(valor: Decimal) -> Decimal:
        return Decimal(str(valor)).quantize(CENTAVOS, rounding=ROUND_HALF_UP)

    @classmethod
    def _normalizar_valor(cls, valor: Decimal) -> Decimal:
        normalizado = cls._quantizar(valor)
        if normalizado <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O valor da despesa deve ser maior que zero.",
            )
        return normalizado

    @staticmethod
    def _validar_periodo(data_inicio: date | None, data_fim: date | None) -> None:
        if data_inicio is not None and data_fim is not None and data_inicio > data_fim:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A data inicial não pode ser maior que a data final.",
            )

    async def criar_despesa(
        self,
        restaurante_id: uuid.UUID,
        data: DespesaCreate,
    ) -> Despesa:
        valor_normalizado = self._normalizar_valor(data.valor)
        despesa = await self.despesa_repo.create(
            restaurante_id=restaurante_id,
            descricao=data.descricao,
            categoria=data.categoria,
            valor=valor_normalizado,
            data_pagamento=data.data_pagamento,
        )
        logger.info(
            "Despesa registrada (restaurante_id=%s, despesa_id=%s, categoria=%s, valor=%s)",
            restaurante_id,
            despesa.id,
            despesa.categoria,
            despesa.valor,
        )
        return despesa

    async def listar_despesas(
        self,
        restaurante_id: uuid.UUID,
        *,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        categoria: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Despesa]:
        self._validar_periodo(data_inicio, data_fim)
        return await self.despesa_repo.list_by_restaurante(
            restaurante_id=restaurante_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            categoria=categoria,
            limit=limit,
            offset=offset,
        )

    async def obter_despesa(
        self,
        restaurante_id: uuid.UUID,
        despesa_id: uuid.UUID,
    ) -> Despesa:
        despesa = await self.despesa_repo.get_by_id_and_restaurante(
            despesa_id=despesa_id,
            restaurante_id=restaurante_id,
        )
        if not despesa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Despesa não encontrada.",
            )
        return despesa

    async def atualizar_despesa(
        self,
        restaurante_id: uuid.UUID,
        despesa_id: uuid.UUID,
        data: DespesaUpdate,
    ) -> Despesa:
        despesa_atual = await self.despesa_repo.get_by_id_and_restaurante(
            despesa_id=despesa_id,
            restaurante_id=restaurante_id,
        )
        if not despesa_atual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Despesa não encontrada.",
            )

        valor_normalizado: Decimal | None = None
        if data.valor is not None:
            valor_normalizado = self._normalizar_valor(data.valor)

        atualizada = await self.despesa_repo.update(
            despesa_id=despesa_id,
            restaurante_id=restaurante_id,
            descricao=data.descricao,
            categoria=data.categoria,
            atualizar_categoria="categoria" in data.model_fields_set,
            valor=valor_normalizado,
            data_pagamento=data.data_pagamento,
        )
        if not atualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Despesa não encontrada.",
            )
        logger.info(
            "Despesa atualizada (restaurante_id=%s, despesa_id=%s)",
            restaurante_id,
            despesa_id,
        )
        return atualizada

    async def excluir_despesa(
        self,
        restaurante_id: uuid.UUID,
        despesa_id: uuid.UUID,
    ) -> None:
        excluida = await self.despesa_repo.delete_by_id_and_restaurante(
            despesa_id=despesa_id,
            restaurante_id=restaurante_id,
        )
        if not excluida:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Despesa não encontrada.",
            )
        logger.info(
            "Despesa excluída (restaurante_id=%s, despesa_id=%s)",
            restaurante_id,
            despesa_id,
        )

    async def obter_resumo(
        self,
        restaurante_id: uuid.UUID,
        *,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> ResumoFinanceiroResponse:
        self._validar_periodo(data_inicio, data_fim)

        inicio_dt = (
            datetime.combine(data_inicio, time.min, tzinfo=UTC)
            if data_inicio is not None
            else None
        )
        fim_dt = (
            datetime.combine(data_fim, time.max, tzinfo=UTC)
            if data_fim is not None
            else None
        )

        total_vendas_raw = await self.comanda_repo.somar_vendas_fechadas_periodo(
            restaurante_id,
            inicio=inicio_dt,
            fim=fim_dt,
        )
        total_despesas_raw = await self.despesa_repo.somar_despesas_periodo(
            restaurante_id,
            inicio=data_inicio,
            fim=data_fim,
        )
        totais_por_categoria = await self.despesa_repo.somar_despesas_por_categoria(
            restaurante_id,
            inicio=data_inicio,
            fim=data_fim,
        )

        total_vendas = self._quantizar(total_vendas_raw)
        total_despesas = self._quantizar(total_despesas_raw)
        saldo = (total_vendas - total_despesas).quantize(CENTAVOS, rounding=ROUND_HALF_UP)
        despesas_por_categoria = {
            categoria: totais_por_categoria.get(categoria, Decimal("0.00"))
            for categoria in CATEGORIAS_DESPESA
        }

        return ResumoFinanceiroResponse(
            restaurante_id=restaurante_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            total_vendas=total_vendas,
            total_despesas=total_despesas,
            saldo=saldo,
            despesas_por_categoria=despesas_por_categoria,
        )
