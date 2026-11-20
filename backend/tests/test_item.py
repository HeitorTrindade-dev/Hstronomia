from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import create_access_token, hash_password
from src.main import app
from src.repositories.dono import DonoRepository
from src.repositories.item import ItemRepository
from src.repositories.restaurante import RestauranteRepository
from src.schemas.item import ItemCreate, ItemUpdate
from src.services.item import ItemService


async def _criar_cenario_dois_restaurantes(db_session: AsyncSession):
    dono_repo = DonoRepository(db_session)
    restaurante_repo = RestauranteRepository(db_session)

    dono_a = await dono_repo.create(
        nome="Dono Alpha",
        email="alpha@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    restaurante_a = await restaurante_repo.create(
        dono_id=dono_a.id,
        nome="Restaurante Alpha",
        slug="restaurante-alpha",
        codigo_garcom="111111",
        codigo_cozinha="222222",
    )

    dono_b = await dono_repo.create(
        nome="Dono Beta",
        email="beta@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    restaurante_b = await restaurante_repo.create(
        dono_id=dono_b.id,
        nome="Restaurante Beta",
        slug="restaurante-beta",
        codigo_garcom="333333",
        codigo_cozinha="444444",
    )
    await db_session.commit()
    return dono_a, restaurante_a, dono_b, restaurante_b


@pytest.mark.asyncio
async def test_item_repository_isolamento_multitenant(db_session: AsyncSession):
    _, rest_a, _, rest_b = await _criar_cenario_dois_restaurantes(db_session)
    repo = ItemRepository(db_session)

    item_a = await repo.create(
        restaurante_id=rest_a.id,
        nome="Hambúrguer Artesanal",
        descricao="Pão brioche e blend 180g",
        preco=Decimal("34.90"),
    )
    item_b = await repo.create(
        restaurante_id=rest_b.id,
        nome="Pizza Margherita",
        descricao=None,
        preco=Decimal("52.00"),
    )
    await db_session.commit()

    # Busca com restaurante correto vs incorreto (IDOR)
    assert await repo.get_by_id_and_restaurante(item_a.id, rest_a.id) is not None
    assert await repo.get_by_id_and_restaurante(item_a.id, rest_b.id) is None

    # Listagem isolada por restaurante
    itens_a = await repo.list_by_restaurante(rest_a.id)
    itens_b = await repo.list_by_restaurante(rest_b.id)
    assert [i.id for i in itens_a] == [item_a.id]
    assert [i.id for i in itens_b] == [item_b.id]

    # Tentativa de update cross-tenant falha silenciosamente (retorna None) sem alterar dados
    tentativa = await repo.update(
        item_id=item_a.id,
        restaurante_id=rest_b.id,
        preco=Decimal("1.00"),
    )
    assert tentativa is None
    recarregado = await repo.get_by_id_and_restaurante(item_a.id, rest_a.id)
    assert recarregado is not None
    assert recarregado.preco == Decimal("34.90")


@pytest.mark.asyncio
async def test_item_service_regras_cadastro_e_alteracao_preco(db_session: AsyncSession):
    _, rest_a, _, rest_b = await _criar_cenario_dois_restaurantes(db_session)
    service = ItemService(db_session)

    criado = await service.criar_item(
        restaurante_id=rest_a.id,
        data=ItemCreate(
            nome="  Suco de Laranja  ",
            descricao="  Natural 500ml  ",
            preco=Decimal("12.5"),
        ),
    )
    await db_session.commit()

    assert isinstance(criado.preco, Decimal)
    assert criado.nome == "Suco de Laranja"
    assert criado.descricao == "Natural 500ml"
    assert criado.preco == Decimal("12.50")
    assert criado.ativo is True
    assert criado.disponivel is True

    # Atualização de preço e remoção de descrição
    atualizado = await service.atualizar_item(
        restaurante_id=rest_a.id,
        item_id=criado.id,
        data=ItemUpdate(preco=Decimal("14.90"), descricao=None),
    )
    await db_session.commit()
    assert atualizado.preco == Decimal("14.90")
    assert atualizado.descricao is None

    # Atualização cross-tenant -> 404
    with pytest.raises(Exception) as exc_info:
        await service.atualizar_item(
            restaurante_id=rest_b.id,
            item_id=criado.id,
            data=ItemUpdate(preco=Decimal("9.90")),
        )
    assert getattr(exc_info.value, "status_code", None) == 404

    # Item desativado não pode ser atualizado -> 400
    criado.ativo = False
    await db_session.commit()
    with pytest.raises(Exception) as exc_inativo:
        await service.atualizar_item(
            restaurante_id=rest_a.id,
            item_id=criado.id,
            data=ItemUpdate(nome="Novo Nome"),
        )
    assert getattr(exc_inativo.value, "status_code", None) == 400


@pytest.mark.asyncio
async def test_endpoints_crud_itens_rbac_e_idor(db_session: AsyncSession):
    dono_a, rest_a, dono_b, rest_b = await _criar_cenario_dois_restaurantes(db_session)

    token_dono_a = create_access_token({"sub": str(dono_a.id), "email": dono_a.email, "role": "dono"})
    token_dono_b = create_access_token({"sub": str(dono_b.id), "email": dono_b.email, "role": "dono"})
    token_garcom_a = create_access_token(
        {"sub": str(rest_a.id), "restaurante_id": str(rest_a.id), "role": "garcom"}
    )
    token_cozinha_a = create_access_token(
        {"sub": str(rest_a.id), "restaurante_id": str(rest_a.id), "role": "cozinha"}
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers_a = {"Authorization": f"Bearer {token_dono_a}"}
            headers_b = {"Authorization": f"Bearer {token_dono_b}"}
            headers_garcom = {"Authorization": f"Bearer {token_garcom_a}"}
            headers_cozinha = {"Authorization": f"Bearer {token_cozinha_a}"}

            # 1. Dono A cria dois itens no cardápio
            res_create_1 = await client.post(
                "/api/v1/itens",
                headers=headers_a,
                json={"nome": "Bife Ancho", "descricao": "300g na brasa", "preco": "78.90"},
            )
            assert res_create_1.status_code == 201
            item_1 = res_create_1.json()
            assert item_1["nome"] == "Bife Ancho"
            assert Decimal(item_1["preco"]) == Decimal("78.90")
            assert item_1["restaurante_id"] == str(rest_a.id)

            res_create_2 = await client.post(
                "/api/v1/itens",
                headers=headers_a,
                json={"nome": "Água com Gás", "preco": "6.50"},
            )
            assert res_create_2.status_code == 201

            # 2. Validações de schema (preço <= 0 e extra="forbid")
            assert (
                await client.post(
                    "/api/v1/itens",
                    headers=headers_a,
                    json={"nome": "Item Grátis", "preco": "0.00"},
                )
            ).status_code == 422
            assert (
                await client.post(
                    "/api/v1/itens",
                    headers=headers_a,
                    json={"nome": "Item Injetado", "preco": "10.00", "restaurante_id": str(rest_b.id)},
                )
            ).status_code == 422

            # 3. BFLA: Garçom e Cozinha NÃO podem criar nem editar itens (403)
            assert (
                await client.post(
                    "/api/v1/itens",
                    headers=headers_garcom,
                    json={"nome": "Tentativa Garçom", "preco": "10.00"},
                )
            ).status_code == 403
            assert (
                await client.put(
                    f"/api/v1/itens/{item_1['id']}",
                    headers=headers_cozinha,
                    json={"preco": "1.00"},
                )
            ).status_code == 403

            # 4. Garçom e Cozinha PODEM listar itens do seu próprio restaurante
            res_list_garcom = await client.get("/api/v1/itens", headers=headers_garcom)
            assert res_list_garcom.status_code == 200
            assert len(res_list_garcom.json()) == 2
            assert [i["nome"] for i in res_list_garcom.json()] == ["Bife Ancho", "Água com Gás"]

            # Garçom tentando listar itens de outro restaurante -> 403
            res_garcom_idor = await client.get(
                f"/api/v1/itens?restaurante_id={rest_b.id}",
                headers=headers_garcom,
            )
            assert res_garcom_idor.status_code == 403

            # 5. Paginação e limite máximo (OWASP A07)
            res_pag = await client.get("/api/v1/itens?limit=1&offset=1", headers=headers_a)
            assert res_pag.status_code == 200
            assert len(res_pag.json()) == 1
            assert (await client.get("/api/v1/itens?limit=101", headers=headers_a)).status_code == 422

            # 6. Dono A atualiza preço e nome do item via PUT
            res_put = await client.put(
                f"/api/v1/itens/{item_1['id']}",
                headers=headers_a,
                json={"nome": "Bife Ancho Premium", "preco": "84.50"},
            )
            assert res_put.status_code == 200
            atualizado = res_put.json()
            assert atualizado["nome"] == "Bife Ancho Premium"
            assert Decimal(atualizado["preco"]) == Decimal("84.50")

            # 7. IDOR: Dono B não pode listar, criar nem editar no Restaurante A
            assert (
                await client.get(f"/api/v1/itens?restaurante_id={rest_a.id}", headers=headers_b)
            ).status_code == 403
            assert (
                await client.post(
                    f"/api/v1/itens?restaurante_id={rest_a.id}",
                    headers=headers_b,
                    json={"nome": "Item Intruso", "preco": "15.00"},
                )
            ).status_code == 403
            assert (
                await client.put(
                    f"/api/v1/itens/{item_1['id']}",
                    headers=headers_b,
                    json={"preco": "0.01"},
                )
            ).status_code == 404

            # Dono B vê apenas sua lista vazia
            res_list_b = await client.get("/api/v1/itens", headers=headers_b)
            assert res_list_b.status_code == 200
            assert res_list_b.json() == []
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dono_com_multiplos_restaurantes_exige_restaurante_id(db_session: AsyncSession):
    dono_a, rest_a, _, _ = await _criar_cenario_dois_restaurantes(db_session)
    rest_repo = RestauranteRepository(db_session)
    rest_a2 = await rest_repo.create(
        dono_id=dono_a.id,
        nome="Restaurante Alpha Filial",
        slug="restaurante-alpha-filial",
        codigo_garcom="555555",
        codigo_cozinha="666666",
    )
    await db_session.commit()

    token_dono_a = create_access_token({"sub": str(dono_a.id), "email": dono_a.email, "role": "dono"})

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers_a = {"Authorization": f"Bearer {token_dono_a}"}

            # Sem restaurante_id quando há múltiplos restaurantes -> 400
            res_amb = await client.get("/api/v1/itens", headers=headers_a)
            assert res_amb.status_code == 400

            # Com restaurante_id explícito da filial -> 201
            res_ok = await client.post(
                f"/api/v1/itens?restaurante_id={rest_a2.id}",
                headers=headers_a,
                json={"nome": "Prato da Filial", "preco": "42.00"},
            )
            assert res_ok.status_code == 201
            assert res_ok.json()["restaurante_id"] == str(rest_a2.id)

            # Restaurante matriz continua sem o item da filial
            res_matriz = await client.get(f"/api/v1/itens?restaurante_id={rest_a.id}", headers=headers_a)
            assert res_matriz.status_code == 200
            assert res_matriz.json() == []
    finally:
        app.dependency_overrides.clear()
