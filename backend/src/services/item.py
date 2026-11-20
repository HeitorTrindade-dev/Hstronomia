import logging
import uuid
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.item import Item
from src.repositories.item import ItemRepository
from src.schemas.item import ItemCreate, ItemUpdate

logger = logging.getLogger(__name__)
CENTAVOS = Decimal("0.01")


class ItemService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.item_repo = ItemRepository(session)

    @staticmethod
    def _normalizar_preco(preco: Decimal) -> Decimal:
        valor = preco.quantize(CENTAVOS, rounding=ROUND_HALF_UP)
        if valor <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O preço do item deve ser maior que zero.",
            )
        return valor

    async def listar_itens(
        self,
        restaurante_id: uuid.UUID,
        *,
        incluir_inativos: bool = False,
        apenas_disponiveis: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Item]:
        return await self.item_repo.list_by_restaurante(
            restaurante_id=restaurante_id,
            apenas_ativos=not incluir_inativos,
            apenas_disponiveis=apenas_disponiveis,
            limit=limit,
            offset=offset,
        )

    async def criar_item(
        self,
        restaurante_id: uuid.UUID,
        data: ItemCreate,
    ) -> Item:
        preco_normalizado = self._normalizar_preco(data.preco)
        return await self.item_repo.create(
            restaurante_id=restaurante_id,
            nome=data.nome,
            descricao=data.descricao,
            preco=preco_normalizado,
            disponivel=data.disponivel,
        )

    async def atualizar_item(
        self,
        restaurante_id: uuid.UUID,
        item_id: uuid.UUID,
        data: ItemUpdate,
    ) -> Item:
        item_atual = await self.item_repo.get_by_id_and_restaurante(item_id, restaurante_id)
        if not item_atual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item não encontrado.",
            )

        if not item_atual.ativo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível alterar um item desativado.",
            )

        preco_normalizado: Decimal | None = None
        if data.preco is not None:
            preco_normalizado = self._normalizar_preco(data.preco)
            if preco_normalizado != item_atual.preco:
                logger.info(
                    "Alteração de preço no cardápio (restaurante_id=%s, item_id=%s, de=%s, para=%s)",
                    restaurante_id,
                    item_id,
                    item_atual.preco,
                    preco_normalizado,
                )

        atualizado = await self.item_repo.update(
            item_id=item_id,
            restaurante_id=restaurante_id,
            nome=data.nome,
            descricao=data.descricao,
            atualizar_descricao="descricao" in data.model_fields_set,
            preco=preco_normalizado,
            disponivel=data.disponivel,
        )
        if not atualizado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item não encontrado.",
            )
        return atualizado

    async def alterar_disponibilidade(
        self,
        restaurante_id: uuid.UUID,
        item_id: uuid.UUID,
        disponivel: bool,
    ) -> Item:
        item_atual = await self.item_repo.get_by_id_and_restaurante(item_id, restaurante_id)
        if not item_atual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item não encontrado.",
            )

        if not item_atual.ativo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível alterar a disponibilidade de um item desativado.",
            )

        atualizado = await self.item_repo.update_disponibilidade(
            item_id=item_id,
            restaurante_id=restaurante_id,
            disponivel=disponivel,
        )
        if not atualizado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item não encontrado.",
            )
        return atualizado

    async def desativar_item(
        self,
        restaurante_id: uuid.UUID,
        item_id: uuid.UUID,
    ) -> Item:
        item_atual = await self.item_repo.get_by_id_and_restaurante(item_id, restaurante_id)
        if not item_atual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item não encontrado.",
            )

        desativado = await self.item_repo.soft_delete(
            item_id=item_id,
            restaurante_id=restaurante_id,
        )
        if not desativado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item não encontrado.",
            )

        logger.info(
            "Item desativado via soft-delete (restaurante_id=%s, item_id=%s)",
            restaurante_id,
            item_id,
        )
        return desativado
