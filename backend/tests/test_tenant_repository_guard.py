import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.base import TenantBaseRepository, TenantIsolationError
from src.repositories.comanda import ComandaRepository
from src.repositories.despesa import DespesaRepository
from src.repositories.item import ItemRepository
from src.repositories.item_comanda import ItemComandaRepository


@pytest.mark.asyncio
async def test_repositorios_operacionais_bloqueiam_metodos_sem_restaurante_id(
    db_session: AsyncSession,
):
    repositorios = [
        ItemRepository(db_session),
        ComandaRepository(db_session),
        ItemComandaRepository(db_session),
        DespesaRepository(db_session),
    ]
    alvo_id = uuid.uuid4()

    for repo in repositorios:
        assert isinstance(repo, TenantBaseRepository)

        with pytest.raises(TenantIsolationError):
            await repo.get_by_id(alvo_id)

        with pytest.raises(TenantIsolationError):
            await repo.get_by("id", alvo_id)

        with pytest.raises(TenantIsolationError):
            await repo.list_by("id", alvo_id)

        with pytest.raises(TenantIsolationError):
            await repo.list_all()

        with pytest.raises(TenantIsolationError):
            await repo.delete_by_id(alvo_id)
