import logging
import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.comanda import Comanda
from src.models.item_comanda import ItemComanda
from src.repositories.comanda import ComandaRepository
from src.repositories.item import ItemRepository
from src.repositories.item_comanda import ItemComandaRepository
from src.schemas.comanda import (
    ComandaCreate,
    ComandaFecharRequest,
    ComandaPreviaResponse,
    ItemComandaCreate,
    ItemComandaResponse,
)

logger = logging.getLogger(__name__)
CENTAVOS = Decimal("0.01")
TAXA_SERVICO_PERCENTUAL = Decimal("0.10")
MAX_VALOR_MONETARIO = Decimal("99999999.99")


class ComandaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.comanda_repo = ComandaRepository(session)
        self.item_comanda_repo = ItemComandaRepository(session)
        self.item_repo = ItemRepository(session)

    @staticmethod
    def quantizar_moeda(valor: Decimal) -> Decimal:
        return valor.quantize(CENTAVOS, rounding=ROUND_HALF_UP)

    async def abrir_comanda(
        self,
        restaurante_id: uuid.UUID,
        data: ComandaCreate,
    ) -> Comanda:
        if data.numero_mesa is not None:
            try:
                comanda_existente = await self.comanda_repo.get_aberta_por_mesa(
                    restaurante_id,
                    data.numero_mesa,
                )
            except MultipleResultsFound:
                logger.warning(
                    "Múltiplas comandas abertas encontradas para a mesa "
                    "(restaurante_id=%s, numero_mesa=%s)",
                    restaurante_id,
                    data.numero_mesa,
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Já existe uma comanda aberta para esta mesa.",
                ) from None

            if comanda_existente is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Já existe uma comanda aberta para esta mesa.",
                )

        comanda = await self.comanda_repo.create(
            restaurante_id=restaurante_id,
            numero_mesa=data.numero_mesa,
            identificador=data.identificador,
            tipo_atendimento=data.tipo_atendimento,
        )
        logger.info(
            "Comanda aberta (restaurante_id=%s, comanda_id=%s, tipo=%s, mesa=%s)",
            restaurante_id,
            comanda.id,
            comanda.tipo_atendimento,
            comanda.numero_mesa,
        )
        return comanda

    async def adicionar_item(
        self,
        restaurante_id: uuid.UUID,
        comanda_id: uuid.UUID,
        data: ItemComandaCreate,
    ) -> ItemComanda:
        comanda = await self.comanda_repo.get_by_id_and_restaurante(
            comanda_id,
            restaurante_id,
        )
        if not comanda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comanda não encontrada.",
            )

        if comanda.status != "aberta":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível adicionar itens a uma comanda que não está aberta.",
            )

        item = await self.item_repo.get_by_id_and_restaurante(
            data.item_id,
            restaurante_id,
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item não encontrado.",
            )

        if not item.ativo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível adicionar um item desativado do cardápio.",
            )

        if not item.disponivel:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item indisponível no cardápio no momento.",
            )

        nome_congelado = item.nome.strip()
        preco_congelado = self.quantizar_moeda(Decimal(item.preco))

        itens = await self.item_comanda_repo.list_by_comanda(comanda.id, restaurante_id)
        subtotal_existente = sum(
            (Decimal(ic.preco_unitario) * Decimal(ic.quantidade) for ic in itens),
            Decimal("0.00"),
        )
        subtotal = self.quantizar_moeda(
            subtotal_existente + (preco_congelado * Decimal(data.quantidade))
        )
        taxa_servico = self.quantizar_moeda(Decimal(comanda.taxa_servico))
        desconto = self.quantizar_moeda(Decimal(comanda.desconto))
        valor_total = max(
            Decimal("0.00"),
            self.quantizar_moeda(subtotal + taxa_servico - desconto),
        )

        if subtotal > MAX_VALOR_MONETARIO or valor_total > MAX_VALOR_MONETARIO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O valor total da comanda excede o limite máximo suportado.",
            )

        item_comanda = await self.item_comanda_repo.create(
            comanda_id=comanda.id,
            restaurante_id=restaurante_id,
            item_id=item.id,
            nome_item=nome_congelado,
            quantidade=data.quantidade,
            preco_unitario=preco_congelado,
            observacao=data.observacao,
        )
        if not item_comanda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comanda não encontrada.",
            )

        await self.comanda_repo.update_totais(
            comanda_id=comanda.id,
            restaurante_id=restaurante_id,
            subtotal=subtotal,
            valor_total=valor_total,
        )

        logger.info(
            "Item adicionado à comanda com congelamento (restaurante_id=%s, comanda_id=%s, "
            "item_id=%s, item_comanda_id=%s, quantidade=%s, preco_unitario=%s)",
            restaurante_id,
            comanda.id,
            item.id,
            item_comanda.id,
            item_comanda.quantidade,
            item_comanda.preco_unitario,
        )
        return item_comanda

    def _calcular_valores_comanda(
        self,
        itens: list[ItemComanda],
        *,
        incluir_taxa_servico: bool,
        desconto: Decimal,
    ) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        subtotal = self.quantizar_moeda(
            sum(
                (Decimal(ic.preco_unitario) * Decimal(ic.quantidade) for ic in itens),
                Decimal("0.00"),
            )
        )
        taxa_servico = (
            self.quantizar_moeda(subtotal * TAXA_SERVICO_PERCENTUAL)
            if incluir_taxa_servico
            else Decimal("0.00")
        )
        desconto_quantizado = self.quantizar_moeda(Decimal(desconto))
        if desconto_quantizado < Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O desconto não pode ser negativo.",
            )

        valor_bruto = self.quantizar_moeda(subtotal + taxa_servico)
        if desconto_quantizado > valor_bruto:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O desconto não pode ser maior que o valor total da comanda.",
            )

        valor_total = self.quantizar_moeda(valor_bruto - desconto_quantizado)
        if subtotal > MAX_VALOR_MONETARIO or valor_total > MAX_VALOR_MONETARIO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O valor total da comanda excede o limite máximo suportado.",
            )

        return subtotal, taxa_servico, desconto_quantizado, valor_total

    async def obter_previa(
        self,
        restaurante_id: uuid.UUID,
        comanda_id: uuid.UUID,
        *,
        incluir_taxa_servico: bool = True,
        desconto: Decimal = Decimal("0.00"),
    ) -> ComandaPreviaResponse:
        comanda = await self.comanda_repo.get_by_id_and_restaurante(
            comanda_id,
            restaurante_id,
        )
        if not comanda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comanda não encontrada.",
            )

        itens = await self.item_comanda_repo.list_by_comanda(comanda.id, restaurante_id)
        subtotal, taxa_servico, desconto_q, valor_total = self._calcular_valores_comanda(
            itens,
            incluir_taxa_servico=incluir_taxa_servico,
            desconto=desconto,
        )

        return ComandaPreviaResponse(
            comanda_id=comanda.id,
            restaurante_id=comanda.restaurante_id,
            numero_mesa=comanda.numero_mesa,
            identificador=comanda.identificador,
            tipo_atendimento=comanda.tipo_atendimento,
            status=comanda.status,
            itens=[ItemComandaResponse.model_validate(ic) for ic in itens],
            subtotal=subtotal,
            incluir_taxa_servico=incluir_taxa_servico,
            taxa_servico=taxa_servico,
            desconto=desconto_q,
            valor_total=valor_total,
        )

    async def fechar_comanda(
        self,
        restaurante_id: uuid.UUID,
        comanda_id: uuid.UUID,
        data: ComandaFecharRequest,
    ) -> Comanda:
        comanda = await self.comanda_repo.get_by_id_and_restaurante(
            comanda_id,
            restaurante_id,
        )
        if not comanda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comanda não encontrada.",
            )

        if comanda.status != "aberta":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Apenas comandas abertas podem ser fechadas.",
            )

        itens = await self.item_comanda_repo.list_by_comanda(comanda.id, restaurante_id)
        subtotal, taxa_servico, desconto_q, valor_total = self._calcular_valores_comanda(
            itens,
            incluir_taxa_servico=data.incluir_taxa_servico,
            desconto=data.desconto,
        )

        fechada = await self.comanda_repo.fechar(
            comanda_id=comanda.id,
            restaurante_id=restaurante_id,
            subtotal=subtotal,
            taxa_servico=taxa_servico,
            desconto=desconto_q,
            valor_total=valor_total,
            metodo_pagamento=data.metodo_pagamento,
            fechado_em=datetime.now(UTC),
        )
        if not fechada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comanda não encontrada.",
            )

        logger.info(
            "Comanda fechada (restaurante_id=%s, comanda_id=%s, subtotal=%s, "
            "taxa_servico=%s, desconto=%s, valor_total=%s, metodo_pagamento=%s)",
            restaurante_id,
            fechada.id,
            fechada.subtotal,
            fechada.taxa_servico,
            fechada.desconto,
            fechada.valor_total,
            fechada.metodo_pagamento,
        )
        return fechada
