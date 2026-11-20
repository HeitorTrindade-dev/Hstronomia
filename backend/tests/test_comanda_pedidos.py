import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import create_access_token, hash_password
from src.main import app
from src.repositories.comanda import ComandaRepository
from src.repositories.dono import DonoRepository
from src.repositories.item import ItemRepository
from src.repositories.item_comanda import ItemComandaRepository
from src.repositories.restaurante import RestauranteRepository
from src.services.comanda import ComandaService


async def _criar_cenario_pedidos(db_session: AsyncSession):
    dono_repo = DonoRepository(db_session)
    rest_repo = RestauranteRepository(db_session)
    item_repo = ItemRepository(db_session)

    dono_a = await dono_repo.create(
        nome="Dono Alpha",
        email="pedidos_alpha@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    rest_a = await rest_repo.create(
        dono_id=dono_a.id,
        nome="Restaurante Alpha",
        slug="pedidos-rest-alpha",
        codigo_garcom="111111",
        codigo_cozinha="222222",
    )

    dono_b = await dono_repo.create(
        nome="Dono Beta",
        email="pedidos_beta@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    rest_b = await rest_repo.create(
        dono_id=dono_b.id,
        nome="Restaurante Beta",
        slug="pedidos-rest-beta",
        codigo_garcom="333333",
        codigo_cozinha="444444",
    )

    item_a1 = await item_repo.create(
        restaurante_id=rest_a.id,
        nome="Filé Parmegiana",
        descricao="Acompanha arroz e fritas",
        preco=Decimal("64.90"),
        disponivel=True,
    )
    item_a2 = await item_repo.create(
        restaurante_id=rest_a.id,
        nome="Suco Natural",
        descricao="Laranja 500ml",
        preco=Decimal("12.50"),
        disponivel=True,
    )
    item_a_pausado = await item_repo.create(
        restaurante_id=rest_a.id,
        nome="Salmão Grelhado",
        descricao=None,
        preco=Decimal("89.00"),
        disponivel=False,
    )
    item_a_inativo = await item_repo.create(
        restaurante_id=rest_a.id,
        nome="Risoto Descontinuado",
        descricao=None,
        preco=Decimal("72.00"),
        disponivel=True,
    )
    await item_repo.soft_delete(item_id=item_a_inativo.id, restaurante_id=rest_a.id)

    item_b1 = await item_repo.create(
        restaurante_id=rest_b.id,
        nome="Lasanha Bolonhesa",
        descricao=None,
        preco=Decimal("49.00"),
        disponivel=True,
    )

    await db_session.commit()

    itens = {
        "a1": item_a1,
        "a2": item_a2,
        "a_pausado": item_a_pausado,
        "a_inativo": item_a_inativo,
        "b1": item_b1,
    }
    return dono_a, rest_a, dono_b, rest_b, itens


def _auth_headers(dono, rest) -> dict[str, dict[str, str]]:
    token_dono = create_access_token(
        {"sub": str(dono.id), "email": dono.email, "role": "dono"}
    )
    token_garcom = create_access_token(
        {"sub": str(rest.id), "restaurante_id": str(rest.id), "role": "garcom"}
    )
    token_cozinha = create_access_token(
        {"sub": str(rest.id), "restaurante_id": str(rest.id), "role": "cozinha"}
    )
    return {
        "dono": {"Authorization": f"Bearer {token_dono}"},
        "garcom": {"Authorization": f"Bearer {token_garcom}"},
        "cozinha": {"Authorization": f"Bearer {token_cozinha}"},
    }


@pytest.mark.asyncio
async def test_abrir_comanda_garcom_e_dono_isolamento(db_session: AsyncSession):
    dono_a, rest_a, _, rest_b, _ = await _criar_cenario_pedidos(db_session)
    headers_a = _auth_headers(dono_a, rest_a)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res_mesa = await client.post(
                "/api/v1/comandas",
                headers=headers_a["garcom"],
                json={
                    "numero_mesa": 4,
                    "identificador": "  Mesa 04  ",
                    "tipo_atendimento": "mesa",
                },
            )
            assert res_mesa.status_code == 201
            body_mesa = res_mesa.json()
            assert body_mesa["status"] == "aberta"
            assert body_mesa["restaurante_id"] == str(rest_a.id)
            assert body_mesa["numero_mesa"] == 4
            assert body_mesa["identificador"] == "Mesa 04"
            assert body_mesa["tipo_atendimento"] == "mesa"
            assert Decimal(body_mesa["subtotal"]) == Decimal("0.00")
            assert Decimal(body_mesa["taxa_servico"]) == Decimal("0.00")
            assert Decimal(body_mesa["desconto"]) == Decimal("0.00")
            assert Decimal(body_mesa["valor_total"]) == Decimal("0.00")

            # Mesa 4 já possui comanda aberta -> 409 Conflict
            res_dup = await client.post(
                "/api/v1/comandas",
                headers=headers_a["garcom"],
                json={"numero_mesa": 4, "tipo_atendimento": "mesa"},
            )
            assert res_dup.status_code == 409

            # Dono abre comanda de balcão e de viagem sem numero_mesa
            res_balcao = await client.post(
                "/api/v1/comandas",
                headers=headers_a["dono"],
                json={"identificador": "Balcão - João", "tipo_atendimento": "balcao"},
            )
            assert res_balcao.status_code == 201
            body_balcao = res_balcao.json()
            assert body_balcao["numero_mesa"] is None
            assert body_balcao["identificador"] == "Balcão - João"
            assert body_balcao["tipo_atendimento"] == "balcao"
            assert body_balcao["status"] == "aberta"

            res_viagem = await client.post(
                "/api/v1/comandas",
                headers=headers_a["dono"],
                json={"identificador": "Retirada #12", "tipo_atendimento": "viagem"},
            )
            assert res_viagem.status_code == 201
            assert res_viagem.json()["tipo_atendimento"] == "viagem"

            # Dono multi-restaurante precisa informar ?restaurante_id=...
            rest_repo = RestauranteRepository(db_session)
            rest_a2 = await rest_repo.create(
                dono_id=dono_a.id,
                nome="Restaurante Alpha Filial",
                slug="pedidos-rest-alpha-filial",
                codigo_garcom="555555",
                codigo_cozinha="666666",
            )
            await db_session.commit()

            res_sem_id = await client.post(
                "/api/v1/comandas",
                headers=headers_a["dono"],
                json={"numero_mesa": 10},
            )
            assert res_sem_id.status_code == 400

            res_filial = await client.post(
                f"/api/v1/comandas?restaurante_id={rest_a2.id}",
                headers=headers_a["dono"],
                json={"numero_mesa": 10},
            )
            assert res_filial.status_code == 201
            assert res_filial.json()["restaurante_id"] == str(rest_a2.id)

            comanda_repo = ComandaRepository(db_session)
            assert await comanda_repo.list_abertas(rest_b.id) == []
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_adicionar_itens_observacao_quantidades_e_recalculo_totais(db_session: AsyncSession):
    dono_a, rest_a, _, _, itens = await _criar_cenario_pedidos(db_session)
    headers_a = _auth_headers(dono_a, rest_a)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res_comanda = await client.post(
                "/api/v1/comandas",
                headers=headers_a["garcom"],
                json={"numero_mesa": 7},
            )
            assert res_comanda.status_code == 201
            comanda_id = res_comanda.json()["id"]

            # Garçom adiciona item com observação (com espaços extras)
            res_item_1 = await client.post(
                f"/api/v1/comandas/{comanda_id}/itens",
                headers=headers_a["garcom"],
                json={
                    "item_id": str(itens["a1"].id),
                    "quantidade": 2,
                    "observacao": "  Sem cebola  ",
                },
            )
            assert res_item_1.status_code == 201
            body_1 = res_item_1.json()
            assert body_1["nome_item"] == "Filé Parmegiana"
            assert Decimal(body_1["preco_unitario"]) == Decimal("64.90")
            assert body_1["quantidade"] == 2
            assert body_1["observacao"] == "Sem cebola"
            assert body_1["status"] == "pendente"

            # Dono adiciona segundo item sem observação
            res_item_2 = await client.post(
                f"/api/v1/comandas/{comanda_id}/itens",
                headers=headers_a["dono"],
                json={
                    "item_id": str(itens["a2"].id),
                    "quantidade": 3,
                },
            )
            assert res_item_2.status_code == 201
            body_2 = res_item_2.json()
            assert body_2["nome_item"] == "Suco Natural"
            assert Decimal(body_2["preco_unitario"]) == Decimal("12.50")
            assert body_2["quantidade"] == 3
            assert body_2["observacao"] is None

            comanda_repo = ComandaRepository(db_session)
            comanda_db = await comanda_repo.get_by_id_and_restaurante(
                uuid.UUID(comanda_id),
                rest_a.id,
                carregar_itens=True,
            )
            assert comanda_db is not None
            assert len(comanda_db.itens) == 2
            # 64.90 * 2 + 12.50 * 3 = 129.80 + 37.50 = 167.30
            assert comanda_db.subtotal == Decimal("167.30")
            assert comanda_db.valor_total == Decimal("167.30")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_congelamento_preco_e_nome_apos_alteracao_cardapio(db_session: AsyncSession):
    dono_a, rest_a, _, _, itens = await _criar_cenario_pedidos(db_session)
    headers_a = _auth_headers(dono_a, rest_a)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res_comanda = await client.post(
                "/api/v1/comandas",
                headers=headers_a["garcom"],
                json={"numero_mesa": 12},
            )
            assert res_comanda.status_code == 201
            comanda_id = uuid.UUID(res_comanda.json()["id"])

            # 1. Adiciona Filé Parmegiana a R$ 64.90 (qty=2 -> 129.80)
            res_add_1 = await client.post(
                f"/api/v1/comandas/{comanda_id}/itens",
                headers=headers_a["garcom"],
                json={"item_id": str(itens["a1"].id), "quantidade": 2},
            )
            assert res_add_1.status_code == 201

            # 2. Dono altera nome e preço do item no cardápio via PUT
            res_put = await client.put(
                f"/api/v1/itens/{itens['a1'].id}",
                headers=headers_a["dono"],
                json={"nome": "Filé Parmegiana Premium", "preco": "89.90"},
            )
            assert res_put.status_code == 200
            assert res_put.json()["nome"] == "Filé Parmegiana Premium"
            assert Decimal(res_put.json()["preco"]) == Decimal("89.90")

            # 3. Item já lançado e totais da comanda permanecem congelados
            item_comanda_repo = ItemComandaRepository(db_session)
            comanda_repo = ComandaRepository(db_session)

            itens_antes = await item_comanda_repo.list_by_comanda(comanda_id, rest_a.id)
            assert len(itens_antes) == 1
            assert itens_antes[0].nome_item == "Filé Parmegiana"
            assert itens_antes[0].preco_unitario == Decimal("64.90")

            comanda_antes = await comanda_repo.get_by_id_and_restaurante(comanda_id, rest_a.id)
            assert comanda_antes is not None
            assert comanda_antes.subtotal == Decimal("129.80")
            assert comanda_antes.valor_total == Decimal("129.80")

            # 4. Novo lançamento do mesmo item usa o novo preço, sem mutar o anterior
            res_add_2 = await client.post(
                f"/api/v1/comandas/{comanda_id}/itens",
                headers=headers_a["garcom"],
                json={"item_id": str(itens["a1"].id), "quantidade": 1},
            )
            assert res_add_2.status_code == 201
            body_2 = res_add_2.json()
            assert body_2["nome_item"] == "Filé Parmegiana Premium"
            assert Decimal(body_2["preco_unitario"]) == Decimal("89.90")

            itens_depois = await item_comanda_repo.list_by_comanda(comanda_id, rest_a.id)
            assert len(itens_depois) == 2
            assert itens_depois[0].nome_item == "Filé Parmegiana"
            assert itens_depois[0].preco_unitario == Decimal("64.90")
            assert itens_depois[1].nome_item == "Filé Parmegiana Premium"
            assert itens_depois[1].preco_unitario == Decimal("89.90")

            comanda_depois = await comanda_repo.get_by_id_and_restaurante(comanda_id, rest_a.id)
            assert comanda_depois is not None
            # 129.80 + 89.90 = 219.70
            assert comanda_depois.subtotal == Decimal("219.70")
            assert comanda_depois.valor_total == Decimal("219.70")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rejeicao_item_indisponivel_inativo_e_inexistente(db_session: AsyncSession):
    dono_a, rest_a, _, _, itens = await _criar_cenario_pedidos(db_session)
    headers_a = _auth_headers(dono_a, rest_a)

    # Cria também um item com ativo=False e disponivel=True para testar verificação de ativo isolada
    item_repo = ItemRepository(db_session)
    item_desativado_disp = await item_repo.create(
        restaurante_id=rest_a.id,
        nome="Item Desativado Disponível",
        descricao=None,
        preco=Decimal("25.00"),
        disponivel=True,
    )
    item_desativado_disp.ativo = False
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res_comanda = await client.post(
                "/api/v1/comandas",
                headers=headers_a["garcom"],
                json={"numero_mesa": 3},
            )
            assert res_comanda.status_code == 201
            comanda_id = uuid.UUID(res_comanda.json()["id"])

            res_pausado = await client.post(
                f"/api/v1/comandas/{comanda_id}/itens",
                headers=headers_a["garcom"],
                json={"item_id": str(itens["a_pausado"].id), "quantidade": 1},
            )
            assert res_pausado.status_code == 400

            res_inativo = await client.post(
                f"/api/v1/comandas/{comanda_id}/itens",
                headers=headers_a["garcom"],
                json={"item_id": str(itens["a_inativo"].id), "quantidade": 1},
            )
            assert res_inativo.status_code == 400

            res_ativo_false = await client.post(
                f"/api/v1/comandas/{comanda_id}/itens",
                headers=headers_a["garcom"],
                json={"item_id": str(item_desativado_disp.id), "quantidade": 1},
            )
            assert res_ativo_false.status_code == 400

            res_inexistente = await client.post(
                f"/api/v1/comandas/{comanda_id}/itens",
                headers=headers_a["garcom"],
                json={"item_id": str(uuid.uuid4()), "quantidade": 1},
            )
            assert res_inexistente.status_code == 404

            item_comanda_repo = ItemComandaRepository(db_session)
            comanda_repo = ComandaRepository(db_session)
            assert await item_comanda_repo.list_by_comanda(comanda_id, rest_a.id) == []
            comanda_db = await comanda_repo.get_by_id_and_restaurante(comanda_id, rest_a.id)
            assert comanda_db is not None
            assert comanda_db.subtotal == Decimal("0.00")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rejeicao_comanda_fechada_cancelada_e_inexistente(db_session: AsyncSession):
    dono_a, rest_a, _, _, itens = await _criar_cenario_pedidos(db_session)
    headers_a = _auth_headers(dono_a, rest_a)

    comanda_repo = ComandaRepository(db_session)
    comanda_fechada = await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=20)
    await comanda_repo.fechar(
        comanda_id=comanda_fechada.id,
        restaurante_id=rest_a.id,
        subtotal=Decimal("0.00"),
        taxa_servico=Decimal("0.00"),
        desconto=Decimal("0.00"),
        valor_total=Decimal("0.00"),
        metodo_pagamento="pix",
        fechado_em=datetime.now(UTC),
    )

    comanda_cancelada = await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=21)
    comanda_cancelada.status = "cancelada"
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res_fechada = await client.post(
                f"/api/v1/comandas/{comanda_fechada.id}/itens",
                headers=headers_a["garcom"],
                json={"item_id": str(itens["a1"].id), "quantidade": 1},
            )
            assert res_fechada.status_code == 400

            res_cancelada = await client.post(
                f"/api/v1/comandas/{comanda_cancelada.id}/itens",
                headers=headers_a["garcom"],
                json={"item_id": str(itens["a1"].id), "quantidade": 1},
            )
            assert res_cancelada.status_code == 400

            res_inexistente = await client.post(
                f"/api/v1/comandas/{uuid.uuid4()}/itens",
                headers=headers_a["garcom"],
                json={"item_id": str(itens["a1"].id), "quantidade": 1},
            )
            assert res_inexistente.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_idor_cross_tenant_comandas_e_itens(db_session: AsyncSession):
    dono_a, rest_a, dono_b, rest_b, itens = await _criar_cenario_pedidos(db_session)
    headers_a = _auth_headers(dono_a, rest_a)
    headers_b = _auth_headers(dono_b, rest_b)

    comanda_repo = ComandaRepository(db_session)
    comanda_a = await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=5)
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Garçom B e Dono B tentando adicionar item B na Comanda A -> 404
            assert (
                await client.post(
                    f"/api/v1/comandas/{comanda_a.id}/itens",
                    headers=headers_b["garcom"],
                    json={"item_id": str(itens["b1"].id), "quantidade": 1},
                )
            ).status_code == 404
            assert (
                await client.post(
                    f"/api/v1/comandas/{comanda_a.id}/itens",
                    headers=headers_b["dono"],
                    json={"item_id": str(itens["b1"].id), "quantidade": 1},
                )
            ).status_code == 404

            # Garçom A e Dono A tentando adicionar Item B na Comanda A -> 404
            assert (
                await client.post(
                    f"/api/v1/comandas/{comanda_a.id}/itens",
                    headers=headers_a["garcom"],
                    json={"item_id": str(itens["b1"].id), "quantidade": 1},
                )
            ).status_code == 404
            assert (
                await client.post(
                    f"/api/v1/comandas/{comanda_a.id}/itens",
                    headers=headers_a["dono"],
                    json={"item_id": str(itens["b1"].id), "quantidade": 1},
                )
            ).status_code == 404

            # Garçom B e Dono B tentando abrir comanda informando restaurante_id de A -> 403
            assert (
                await client.post(
                    f"/api/v1/comandas?restaurante_id={rest_a.id}",
                    headers=headers_b["garcom"],
                    json={"numero_mesa": 99},
                )
            ).status_code == 403
            assert (
                await client.post(
                    f"/api/v1/comandas?restaurante_id={rest_a.id}",
                    headers=headers_b["dono"],
                    json={"numero_mesa": 99},
                )
            ).status_code == 403

            item_comanda_repo = ItemComandaRepository(db_session)
            assert await item_comanda_repo.list_by_comanda(comanda_a.id, rest_a.id) == []
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rbac_cozinha_bloqueada_e_nao_autenticado(db_session: AsyncSession):
    dono_a, rest_a, _, _, itens = await _criar_cenario_pedidos(db_session)
    headers_a = _auth_headers(dono_a, rest_a)

    comanda_repo = ComandaRepository(db_session)
    comanda_a = await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=8)
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Cozinha bloqueada com 403 em ambos os endpoints
            res_coz_open = await client.post(
                "/api/v1/comandas",
                headers=headers_a["cozinha"],
                json={"numero_mesa": 9},
            )
            assert res_coz_open.status_code == 403

            res_coz_add = await client.post(
                f"/api/v1/comandas/{comanda_a.id}/itens",
                headers=headers_a["cozinha"],
                json={"item_id": str(itens["a1"].id), "quantidade": 1},
            )
            assert res_coz_add.status_code == 403

            # Sem Authorization header -> 401/403
            res_unauth_open = await client.post(
                "/api/v1/comandas",
                json={"numero_mesa": 9},
            )
            assert res_unauth_open.status_code in (401, 403)

            res_unauth_add = await client.post(
                f"/api/v1/comandas/{comanda_a.id}/itens",
                json={"item_id": str(itens["a1"].id), "quantidade": 1},
            )
            assert res_unauth_add.status_code in (401, 403)

            # Token inválido -> 401
            bad_headers = {"Authorization": "Bearer token.invalido"}
            assert (
                await client.post(
                    "/api/v1/comandas",
                    headers=bad_headers,
                    json={"numero_mesa": 9},
                )
            ).status_code == 401
            assert (
                await client.post(
                    f"/api/v1/comandas/{comanda_a.id}/itens",
                    headers=bad_headers,
                    json={"item_id": str(itens["a1"].id), "quantidade": 1},
                )
            ).status_code == 401

            # Garçom e Dono obtêm 201 em ambos os endpoints
            res_g_open = await client.post(
                "/api/v1/comandas",
                headers=headers_a["garcom"],
                json={"numero_mesa": 15},
            )
            assert res_g_open.status_code == 201
            assert (
                await client.post(
                    f"/api/v1/comandas/{res_g_open.json()['id']}/itens",
                    headers=headers_a["garcom"],
                    json={"item_id": str(itens["a1"].id), "quantidade": 1},
                )
            ).status_code == 201

            res_d_open = await client.post(
                "/api/v1/comandas",
                headers=headers_a["dono"],
                json={"numero_mesa": 16},
            )
            assert res_d_open.status_code == 201
            assert (
                await client.post(
                    f"/api/v1/comandas/{res_d_open.json()['id']}/itens",
                    headers=headers_a["dono"],
                    json={"item_id": str(itens["a2"].id), "quantidade": 1},
                )
            ).status_code == 201
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_validacoes_schema_extra_forbid_e_limites(db_session: AsyncSession):
    dono_a, rest_a, _, _, itens = await _criar_cenario_pedidos(db_session)
    headers_a = _auth_headers(dono_a, rest_a)

    comanda_repo = ComandaRepository(db_session)
    comanda_a = await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=2)
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Extra fields proibidos na abertura de comanda
            for payload in [
                {"numero_mesa": 30, "restaurante_id": str(rest_a.id)},
                {"numero_mesa": 30, "status": "fechada"},
                {"numero_mesa": 30, "subtotal": "999.00"},
                {"numero_mesa": 30, "valor_total": "999.00"},
            ]:
                assert (
                    await client.post(
                        "/api/v1/comandas",
                        headers=headers_a["garcom"],
                        json=payload,
                    )
                ).status_code == 422

            # Sem numero_mesa nem identificador (ou identificador vazio) -> 422
            assert (
                await client.post(
                    "/api/v1/comandas",
                    headers=headers_a["garcom"],
                    json={"tipo_atendimento": "mesa"},
                )
            ).status_code == 422
            assert (
                await client.post(
                    "/api/v1/comandas",
                    headers=headers_a["garcom"],
                    json={"identificador": "   ", "tipo_atendimento": "balcao"},
                )
            ).status_code == 422

            # tipo_atendimento inválido ou numero_mesa <= 0 -> 422
            assert (
                await client.post(
                    "/api/v1/comandas",
                    headers=headers_a["garcom"],
                    json={"identificador": "Delivery", "tipo_atendimento": "delivery"},
                )
            ).status_code == 422
            assert (
                await client.post(
                    "/api/v1/comandas",
                    headers=headers_a["garcom"],
                    json={"numero_mesa": 0},
                )
            ).status_code == 422

            # Extra fields proibidos na adição de itens (mass assignment)
            for payload in [
                {"item_id": str(itens["a1"].id), "preco_unitario": "0.01"},
                {"item_id": str(itens["a1"].id), "nome_item": "Hack"},
                {"item_id": str(itens["a1"].id), "status": "entregue"},
                {"item_id": str(itens["a1"].id), "comanda_id": str(comanda_a.id)},
                {"item_id": str(itens["a1"].id), "restaurante_id": str(rest_a.id)},
            ]:
                assert (
                    await client.post(
                        f"/api/v1/comandas/{comanda_a.id}/itens",
                        headers=headers_a["garcom"],
                        json=payload,
                    )
                ).status_code == 422

            # Quantidade inválida (<= 0) -> 422
            for qtd in (0, -2):
                assert (
                    await client.post(
                        f"/api/v1/comandas/{comanda_a.id}/itens",
                        headers=headers_a["garcom"],
                        json={"item_id": str(itens["a1"].id), "quantidade": qtd},
                    )
                ).status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_precisao_decimal_e_arredondamento_round_half_up(db_session: AsyncSession):
    dono_a, rest_a, _, _, _ = await _criar_cenario_pedidos(db_session)
    headers_a = _auth_headers(dono_a, rest_a)

    item_repo = ItemRepository(db_session)
    item_1999 = await item_repo.create(
        restaurante_id=rest_a.id,
        nome="Porção 19.99",
        descricao=None,
        preco=Decimal("19.99"),
    )
    item_010 = await item_repo.create(
        restaurante_id=rest_a.id,
        nome="Adicional 0.10",
        descricao=None,
        preco=Decimal("0.10"),
    )
    item_020 = await item_repo.create(
        restaurante_id=rest_a.id,
        nome="Adicional 0.20",
        descricao=None,
        preco=Decimal("0.20"),
    )
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res_c1 = await client.post(
                "/api/v1/comandas",
                headers=headers_a["garcom"],
                json={"numero_mesa": 40},
            )
            c1_id = uuid.UUID(res_c1.json()["id"])

            assert (
                await client.post(
                    f"/api/v1/comandas/{c1_id}/itens",
                    headers=headers_a["garcom"],
                    json={"item_id": str(item_1999.id), "quantidade": 3},
                )
            ).status_code == 201

            comanda_repo = ComandaRepository(db_session)
            c1_db = await comanda_repo.get_by_id_and_restaurante(c1_id, rest_a.id)
            assert c1_db is not None
            assert isinstance(c1_db.subtotal, Decimal)
            assert c1_db.subtotal == Decimal("59.97")
            assert c1_db.valor_total == Decimal("59.97")

            # 0.10 + 0.20 == 0.30 sem erro de ponto flutuante
            res_c2 = await client.post(
                "/api/v1/comandas",
                headers=headers_a["garcom"],
                json={"numero_mesa": 41},
            )
            c2_id = uuid.UUID(res_c2.json()["id"])
            assert (
                await client.post(
                    f"/api/v1/comandas/{c2_id}/itens",
                    headers=headers_a["garcom"],
                    json={"item_id": str(item_010.id), "quantidade": 1},
                )
            ).status_code == 201
            assert (
                await client.post(
                    f"/api/v1/comandas/{c2_id}/itens",
                    headers=headers_a["garcom"],
                    json={"item_id": str(item_020.id), "quantidade": 1},
                )
            ).status_code == 201

            c2_db = await comanda_repo.get_by_id_and_restaurante(c2_id, rest_a.id)
            assert c2_db is not None
            assert isinstance(c2_db.subtotal, Decimal)
            assert c2_db.subtotal == Decimal("0.30")
            assert c2_db.valor_total == Decimal("0.30")
    finally:
        app.dependency_overrides.clear()

    # Teste unitário direto da regra ROUND_HALF_UP (diferente de ROUND_HALF_EVEN em 10.005)
    r1 = ComandaService.quantizar_moeda(Decimal("10.005"))
    r2 = ComandaService.quantizar_moeda(Decimal("10.015"))
    r3 = ComandaService.quantizar_moeda(Decimal("10.004"))
    assert isinstance(r1, Decimal)
    assert r1 == Decimal("10.01")
    assert r2 == Decimal("10.02")
    assert r3 == Decimal("10.00")


@pytest.mark.asyncio
async def test_abrir_comanda_duplicidade_concorrente_retorna_409(db_session: AsyncSession):
    from sqlalchemy.exc import IntegrityError

    dono_a, rest_a, _, _, _ = await _criar_cenario_pedidos(db_session)
    headers_a = _auth_headers(dono_a, rest_a)

    comanda_repo = ComandaRepository(db_session)
    await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=42)
    await db_session.commit()

    # O índice único parcial uq_comanda_restaurante_mesa_aberta impede duplicidade direto no banco
    with pytest.raises(IntegrityError):
        await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=42)
    await db_session.rollback()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            res = await client.post(
                "/api/v1/comandas",
                headers=headers_a["garcom"],
                json={"numero_mesa": 42, "tipo_atendimento": "mesa"},
            )
            assert res.status_code == 409
            assert res.json()["detail"] == "Já existe uma comanda aberta para esta mesa."
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_adicionar_item_overflow_numeric_retorna_400_sem_mutacao(db_session: AsyncSession):
    dono_a, rest_a, _, _, _ = await _criar_cenario_pedidos(db_session)
    headers_a = _auth_headers(dono_a, rest_a)

    item_repo = ItemRepository(db_session)
    item_caro = await item_repo.create(
        restaurante_id=rest_a.id,
        nome="Vinho Raro",
        descricao=None,
        preco=Decimal("9999999.99"),
    )
    item_limite = await item_repo.create(
        restaurante_id=rest_a.id,
        nome="Reserva Especial",
        descricao=None,
        preco=Decimal("99999990.00"),
    )

    comanda_repo = ComandaRepository(db_session)
    comanda_sub = await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=51)
    comanda_tot = await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=52)
    await comanda_repo.update_totais(
        comanda_id=comanda_tot.id,
        restaurante_id=rest_a.id,
        subtotal=Decimal("0.00"),
        taxa_servico=Decimal("20.00"),
        valor_total=Decimal("20.00"),
    )
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Overflow de subtotal (9999999.99 * 999 > 99999999.99) -> 400
            res_sub = await client.post(
                f"/api/v1/comandas/{comanda_sub.id}/itens",
                headers=headers_a["garcom"],
                json={"item_id": str(item_caro.id), "quantidade": 999},
            )
            assert res_sub.status_code == 400

            # 2. Subtotal dentro do limite (99999990.00), mas valor_total com taxa_servico (20.00) excede -> 400
            res_tot = await client.post(
                f"/api/v1/comandas/{comanda_tot.id}/itens",
                headers=headers_a["garcom"],
                json={"item_id": str(item_limite.id), "quantidade": 1},
            )
            assert res_tot.status_code == 400

            item_comanda_repo = ItemComandaRepository(db_session)
            assert await item_comanda_repo.list_by_comanda(comanda_sub.id, rest_a.id) == []
            assert await item_comanda_repo.list_by_comanda(comanda_tot.id, rest_a.id) == []

            c_sub_db = await comanda_repo.get_by_id_and_restaurante(comanda_sub.id, rest_a.id)
            assert c_sub_db is not None
            assert c_sub_db.subtotal == Decimal("0.00")
            assert c_sub_db.valor_total == Decimal("0.00")

            c_tot_db = await comanda_repo.get_by_id_and_restaurante(comanda_tot.id, rest_a.id)
            assert c_tot_db is not None
            assert c_tot_db.subtotal == Decimal("0.00")
            assert c_tot_db.valor_total == Decimal("20.00")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_validacoes_strict_int_e_null_bytes_retornam_422(db_session: AsyncSession):
    dono_a, rest_a, _, _, itens = await _criar_cenario_pedidos(db_session)
    headers_a = _auth_headers(dono_a, rest_a)

    comanda_repo = ComandaRepository(db_session)
    comanda_a = await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=60)
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # numero_mesa com bool ou float -> 422
            for mesa_invalida in (True, False, 1.0, 1.5):
                res = await client.post(
                    "/api/v1/comandas",
                    headers=headers_a["garcom"],
                    json={"numero_mesa": mesa_invalida},
                )
                assert res.status_code == 422

            # quantidade com bool ou float -> 422
            for qtd_invalida in (True, False, 1.0, 1.5):
                res = await client.post(
                    f"/api/v1/comandas/{comanda_a.id}/itens",
                    headers=headers_a["garcom"],
                    json={"item_id": str(itens["a1"].id), "quantidade": qtd_invalida},
                )
                assert res.status_code == 422

            # Null bytes (\x00) em identificador e observacao -> 422
            res_ident_nul = await client.post(
                "/api/v1/comandas",
                headers=headers_a["garcom"],
                json={"identificador": "Mesa\x00VIP", "tipo_atendimento": "balcao"},
            )
            assert res_ident_nul.status_code == 422

            res_obs_nul = await client.post(
                f"/api/v1/comandas/{comanda_a.id}/itens",
                headers=headers_a["garcom"],
                json={
                    "item_id": str(itens["a1"].id),
                    "quantidade": 1,
                    "observacao": "Sem\x00cebola",
                },
            )
            assert res_obs_nul.status_code == 422
    finally:
        app.dependency_overrides.clear()
