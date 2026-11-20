import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.base import TenantIsolationError
from src.repositories.dono import DonoRepository
from src.repositories.restaurante import RestauranteRepository


@pytest.mark.asyncio
async def test_dono_repository_crud(db_session: AsyncSession):
    repo = DonoRepository(db_session)

    # 1. Criar Dono
    dono = await repo.create(
        nome="Carlos Silva",
        email="CARLOS@restaurante.com",
        senha_hash="hash_super_seguro",
    )
    assert dono.id is not None
    assert dono.nome == "Carlos Silva"
    assert dono.email == "carlos@restaurante.com"

    # 2. Buscar por email
    encontrado = await repo.get_by_email("carlos@restaurante.com")
    assert encontrado is not None
    assert encontrado.id == dono.id

    # 3. Buscar por ID (herdado do BaseRepository)
    por_id = await repo.get_by_id(dono.id)
    assert por_id is not None
    assert por_id.email == "carlos@restaurante.com"

    # 4. List all e Delete by ID bloqueados contra exposição global e deleção em cascata
    with pytest.raises(TenantIsolationError):
        await repo.list_all()

    with pytest.raises(TenantIsolationError):
        await repo.delete_by_id(dono.id)


@pytest.mark.asyncio
async def test_restaurante_repository_crud_e_idor(db_session: AsyncSession):
    dono_repo = DonoRepository(db_session)
    rest_repo = RestauranteRepository(db_session)

    dono = await dono_repo.create(
        nome="Maria Souza",
        email="maria@bistrot.com",
        senha_hash="hash_maria",
    )

    # 1. Criar Restaurante
    restaurante = await rest_repo.create(
        dono_id=dono.id,
        nome="Bistrô da Maria",
        slug="BISTRO-MARIA",
        codigo_garcom="123456",
        codigo_cozinha="654321",
    )
    assert restaurante.id is not None
    assert restaurante.slug == "bistro-maria"
    assert restaurante.dono_id == dono.id

    # 2. Buscar por slug
    por_slug = await rest_repo.get_by_slug("bistro-maria")
    assert por_slug is not None
    assert por_slug.id == restaurante.id

    # 3. Buscar por ID (herdado do BaseRepository)
    por_id = await rest_repo.get_by_id(restaurante.id)
    assert por_id is not None
    assert por_id.nome == "Bistrô da Maria"

    # 4. Listar por dono_id
    lista = await rest_repo.get_by_dono_id(dono.id)
    assert len(lista) == 1
    assert lista[0].id == restaurante.id

    # 5. Atualizar PINs com dono correto
    atualizado = await rest_repo.update_pins(
        restaurante_id=restaurante.id,
        dono_id=dono.id,
        codigo_garcom="999888",
    )
    assert atualizado is not None
    assert atualizado.codigo_garcom == "999888"

    # 6. Tentativa de IDOR: dono intruso
    dono_intruso_id = uuid.uuid4()
    bloqueado = await rest_repo.update_pins(
        restaurante_id=restaurante.id,
        dono_id=dono_intruso_id,
        codigo_garcom="000000",
    )
    assert bloqueado is None
