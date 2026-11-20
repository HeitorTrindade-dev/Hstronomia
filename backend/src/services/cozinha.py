import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.item_comanda import ItemComanda
from src.repositories.item_comanda import ItemComandaRepository
from src.schemas.cozinha import (
    CozinhaPedidoResponse,
    StatusFilaCozinha,
    StatusItemCozinha,
)

logger = logging.getLogger(__name__)

TRANSICOES_VALIDAS_KDS: dict[str, str] = {
    "pendente": "em_preparo",
    "em_preparo": "pronto",
    "pronto": "entregue",
}


class CozinhaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.item_comanda_repo = ItemComandaRepository(session)

    @staticmethod
    def _to_response(item_comanda: ItemComanda) -> CozinhaPedidoResponse:
        return CozinhaPedidoResponse(
            id=item_comanda.id,
            comanda_id=item_comanda.comanda_id,
            item_id=item_comanda.item_id,
            nome_item=item_comanda.nome_item,
            quantidade=item_comanda.quantidade,
            observacao=item_comanda.observacao,
            status=item_comanda.status,
            criado_em=item_comanda.criado_em,
            numero_mesa=item_comanda.comanda.numero_mesa,
            identificador=item_comanda.comanda.identificador,
            tipo_atendimento=item_comanda.comanda.tipo_atendimento,
        )

    async def listar_pedidos(
        self,
        restaurante_id: uuid.UUID,
        *,
        status_filtro: StatusFilaCozinha | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CozinhaPedidoResponse]:
        statuses: tuple[str, ...] = (
            (status_filtro,) if status_filtro is not None else ("pendente", "em_preparo")
        )
        itens = await self.item_comanda_repo.list_por_status_cozinha(
            restaurante_id=restaurante_id,
            statuses=statuses,
            limit=limit,
            offset=offset,
        )
        return [self._to_response(item) for item in itens]

    async def atualizar_status_pedido(
        self,
        restaurante_id: uuid.UUID,
        item_comanda_id: uuid.UUID,
        novo_status: StatusItemCozinha,
    ) -> CozinhaPedidoResponse:
        item_atual = await self.item_comanda_repo.get_by_id_and_restaurante(
            item_comanda_id,
            restaurante_id,
            carregar_comanda=True,
        )
        if not item_atual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado.",
            )

        if item_atual.comanda.status != "aberta":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível alterar o status de pedido de uma comanda fechada ou cancelada.",
            )

        status_anterior = item_atual.status
        proximo_esperado = TRANSICOES_VALIDAS_KDS.get(status_anterior)
        if proximo_esperado != novo_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transição de status inválida de '{status_anterior}' para '{novo_status}'.",
            )

        atualizado = await self.item_comanda_repo.update_status(
            item_comanda_id=item_comanda_id,
            restaurante_id=restaurante_id,
            status=novo_status,
            carregar_comanda=True,
        )
        if not atualizado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado.",
            )

        logger.info(
            "Status de pedido KDS atualizado (restaurante_id=%s, item_comanda_id=%s, de=%s, para=%s)",
            restaurante_id,
            item_comanda_id,
            status_anterior,
            novo_status,
        )
        return self._to_response(atualizado)
