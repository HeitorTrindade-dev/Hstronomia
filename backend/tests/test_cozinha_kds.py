import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import (
    create_access_token,
    create_operational_token,
    hash_password,
)
from src.main import app
from src.models.comanda import Comanda
from src.models.item_comanda import ItemComanda
from src.repositories.comanda import ComandaRepository
from src.repositories.dono import DonoRepository
from src.repositories.item import ItemRepository
from src.repositories.item_comanda import ItemComandaRepository
from src.repositories.restaurante import RestauranteRepository
from src.services.cozinha import CozinhaService


async def _criar_cenario_kds(db_session: AsyncSession):
    dono_repo = DonoRepository(db_session)
    rest_repo = RestauranteRepository(db_session)
    item_repo = ItemRepository(db_session)
    comanda_repo = ComandaRepository(db_session)

    dono_a = await dono_repo.create(
        nome="Dono Alpha",
        email="kds_alpha@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    rest_a1 = await rest_repo.create(
        dono_id=dono_a.id,
        nome="Restaurante Alpha 1",
        slug="kds-alpha-1",
        codigo_garcom="111111",
        codigo_cozinha="222222",
    )
    item_a1 = await item_repo.create(
        restaurante_id=rest_a1.id,
        nome="Filé Parmegiana",
        descricao="Arroz e fritas",
        preco=Decimal("64.90"),
    )
    item_a2 = await item_repo.create(
        restaurante_id=rest_a1.id,
        nome="Suco de Laranja",
        descricao=None,
        preco=Decimal("12.00"),
    )

    dono_b = await dono_repo.create(
        nome="Dono Beta",
        email="kds_beta@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    rest_b = await rest_repo.create(
        dono_id=dono_b.id,
        nome="Restaurante Beta",
        slug="kds-beta",
        codigo_garcom="333333",
        codigo_cozinha="444444",
    )
    item_b = await item_repo.create(
        restaurante_id=rest_b.id,
        nome="Lasanha Bolonhesa",
        descricao=None,
        preco=Decimal("49.00"),
    )

    comanda_mesa_a = await comanda_repo.create(
        restaurante_id=rest_a1.id,
        numero_mesa=4,
        identificador="Mesa 04",
        tipo_atendimento="mesa",
    )
    comanda_balcao_a = await comanda_repo.create(
        restaurante_id=rest_a1.id,
        numero_mesa=None,
        identificador="Balcão - Maria",
        tipo_atendimento="balcao",
    )
    comanda_fechada_a = Comanda(
        restaurante_id=rest_a1.id,
        numero_mesa=9,
        identificador="Mesa 09",
        tipo_atendimento="mesa",
        status="fechada",
    )
    comanda_cancelada_a = Comanda(
        restaurante_id=rest_a1.id,
        numero_mesa=10,
        identificador="Mesa 10",
        tipo_atendimento="mesa",
        status="cancelada",
    )
    comanda_b = await comanda_repo.create(
        restaurante_id=rest_b.id,
        numero_mesa=1,
        identificador="Mesa 01 B",
        tipo_atendimento="mesa",
    )
    db_session.add_all([comanda_fechada_a, comanda_cancelada_a])
    await db_session.commit()

    return {
        "dono_a": dono_a,
        "rest_a1": rest_a1,
        "item_a1": item_a1,
        "item_a2": item_a2,
        "dono_b": dono_b,
        "rest_b": rest_b,
        "item_b": item_b,
        "comanda_mesa_a": comanda_mesa_a,
        "comanda_balcao_a": comanda_balcao_a,
        "comanda_fechada_a": comanda_fechada_a,
        "comanda_cancelada_a": comanda_cancelada_a,
        "comanda_b": comanda_b,
    }


async def _criar_item_comanda(
    db_session: AsyncSession,
    *,
    comanda_id: uuid.UUID,
    item_id: uuid.UUID,
    nome_item: str,
    quantidade: int = 1,
    preco_unitario: Decimal = Decimal("30.00"),
    observacao: str | None = None,
    status_item: str = "pendente",
    criado_em: datetime | None = None,
) -> ItemComanda:
    registro = ItemComanda(
        comanda_id=comanda_id,
        item_id=item_id,
        nome_item=nome_item,
        quantidade=quantidade,
        preco_unitario=preco_unitario,
        observacao=observacao,
        status=status_item,
    )
    if criado_em is not None:
        registro.criado_em = criado_em
    db_session.add(registro)
    await db_session.commit()
    return registro


@pytest.mark.asyncio
async def test_kds_fila_fifo_contexto_filtros_e_paginacao(db_session: AsyncSession):
    cenario = await _criar_cenario_kds(db_session)
    base_time = datetime(2026, 11, 20, 12, 0, 0, tzinfo=UTC)

    # Itens elegíveis para a fila de A (em_preparo mais antigo que pendente)
    pedido_1 = await _criar_item_comanda(
        db_session,
        comanda_id=cenario["comanda_mesa_a"].id,
        item_id=cenario["item_a1"].id,
        nome_item="Filé Parmegiana",
        quantidade=2,
        observacao="Sem cebola",
        status_item="em_preparo",
        criado_em=base_time,
    )
    pedido_2 = await _criar_item_comanda(
        db_session,
        comanda_id=cenario["comanda_balcao_a"].id,
        item_id=cenario["item_a2"].id,
        nome_item="Suco de Laranja",
        quantidade=1,
        observacao="Com gelo e açúcar",
        status_item="pendente",
        criado_em=base_time + timedelta(seconds=10),
    )
    pedido_3 = await _criar_item_comanda(
        db_session,
        comanda_id=cenario["comanda_mesa_a"].id,
        item_id=cenario["item_a2"].id,
        nome_item="Suco de Laranja",
        quantidade=3,
        observacao=None,
        status_item="pendente",
        criado_em=base_time + timedelta(seconds=20),
    )

    # Itens que NÃO devem aparecer na fila padrão (pendente/em_preparo)
    pedido_pronto = await _criar_item_comanda(
        db_session,
        comanda_id=cenario["comanda_mesa_a"].id,
        item_id=cenario["item_a1"].id,
        nome_item="Pronto não listado",
        status_item="pronto",
        criado_em=base_time + timedelta(seconds=1),
    )
    await _criar_item_comanda(
        db_session,
        comanda_id=cenario["comanda_mesa_a"].id,
        item_id=cenario["item_a1"].id,
        nome_item="Entregue não listado",
        status_item="entregue",
        criado_em=base_time + timedelta(seconds=2),
    )
    await _criar_item_comanda(
        db_session,
        comanda_id=cenario["comanda_fechada_a"].id,
        item_id=cenario["item_a1"].id,
        nome_item="Comanda Fechada",
        status_item="pendente",
        criado_em=base_time + timedelta(seconds=3),
    )
    await _criar_item_comanda(
        db_session,
        comanda_id=cenario["comanda_cancelada_a"].id,
        item_id=cenario["item_a1"].id,
        nome_item="Comanda Cancelada",
        status_item="pendente",
        criado_em=base_time + timedelta(seconds=4),
    )
    await _criar_item_comanda(
        db_session,
        comanda_id=cenario["comanda_b"].id,
        item_id=cenario["item_b"].id,
        nome_item="Lasanha Outro Tenant",
        status_item="pendente",
        criado_em=base_time + timedelta(seconds=5),
    )

    token_cozinha_a = create_operational_token(
        cenario["rest_a1"].id,
        "cozinha",
        cenario["rest_a1"].codigo_cozinha,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token_cozinha_a}"}

            # Listagem padrão: FIFO (pedido_1 -> pedido_2 -> pedido_3)
            res = await client.get("/api/v1/cozinha/pedidos", headers=headers)
            assert res.status_code == 200
            dados = res.json()
            assert [item["id"] for item in dados] == [
                str(pedido_1.id),
                str(pedido_2.id),
                str(pedido_3.id),
            ]

            # Verifica contexto completo da comanda e minimização de dados
            assert dados[0]["numero_mesa"] == 4
            assert dados[0]["identificador"] == "Mesa 04"
            assert dados[0]["tipo_atendimento"] == "mesa"
            assert dados[0]["observacao"] == "Sem cebola"
            assert dados[0]["quantidade"] == 2
            assert dados[0]["status"] == "em_preparo"
            assert "preco_unitario" not in dados[0]

            assert dados[1]["numero_mesa"] is None
            assert dados[1]["identificador"] == "Balcão - Maria"
            assert dados[1]["tipo_atendimento"] == "balcao"
            assert dados[1]["observacao"] == "Com gelo e açúcar"

            # Filtro por ?status=pendente e ?status=em_preparo
            res_pendente = await client.get(
                "/api/v1/cozinha/pedidos",
                headers=headers,
                params={"status": "pendente"},
            )
            assert res_pendente.status_code == 200
            assert [i["id"] for i in res_pendente.json()] == [str(pedido_2.id), str(pedido_3.id)]

            res_preparo = await client.get(
                "/api/v1/cozinha/pedidos",
                headers=headers,
                params={"status": "em_preparo"},
            )
            assert res_preparo.status_code == 200
            assert [i["id"] for i in res_preparo.json()] == [str(pedido_1.id)]

            # Filtro por ?status=pronto é válido (200), enquanto ?status=entregue na fila é inválido (422)
            res_pronto = await client.get(
                "/api/v1/cozinha/pedidos",
                headers=headers,
                params={"status": "pronto"},
            )
            assert res_pronto.status_code == 200
            assert [i["id"] for i in res_pronto.json()] == [str(pedido_pronto.id)]

            assert (
                await client.get(
                    "/api/v1/cozinha/pedidos",
                    headers=headers,
                    params={"status": "entregue"},
                )
            ).status_code == 422

            # Paginação válida e limites inválidos
            res_pag = await client.get(
                "/api/v1/cozinha/pedidos",
                headers=headers,
                params={"limit": 1, "offset": 1},
            )
            assert res_pag.status_code == 200
            assert [i["id"] for i in res_pag.json()] == [str(pedido_2.id)]

            assert (
                await client.get(
                    "/api/v1/cozinha/pedidos",
                    headers=headers,
                    params={"limit": 101},
                )
            ).status_code == 422
            assert (
                await client.get(
                    "/api/v1/cozinha/pedidos",
                    headers=headers,
                    params={"limit": 0},
                )
            ).status_code == 422
            assert (
                await client.get(
                    "/api/v1/cozinha/pedidos",
                    headers=headers,
                    params={"offset": -1},
                )
            ).status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_kds_maquina_estados_estrita_e_comanda_fechada(db_session: AsyncSession):
    cenario = await _criar_cenario_kds(db_session)
    pedido = await _criar_item_comanda(
        db_session,
        comanda_id=cenario["comanda_mesa_a"].id,
        item_id=cenario["item_a1"].id,
        nome_item="Filé Parmegiana",
        status_item="pendente",
    )
    pedido_fechada = await _criar_item_comanda(
        db_session,
        comanda_id=cenario["comanda_fechada_a"].id,
        item_id=cenario["item_a1"].id,
        nome_item="Item Comanda Fechada",
        status_item="pendente",
    )
    pedido_cancelada = await _criar_item_comanda(
        db_session,
        comanda_id=cenario["comanda_cancelada_a"].id,
        item_id=cenario["item_a1"].id,
        nome_item="Item Comanda Cancelada",
        status_item="pendente",
    )

    token_cozinha_a = create_operational_token(
        cenario["rest_a1"].id,
        "cozinha",
        cenario["rest_a1"].codigo_cozinha,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token_cozinha_a}"}
            url = f"/api/v1/cozinha/pedidos/{pedido.id}/status"

            # Comandas fechada ou cancelada não permitem alteração -> 400
            assert (
                await client.patch(
                    f"/api/v1/cozinha/pedidos/{pedido_fechada.id}/status",
                    headers=headers,
                    json={"status": "em_preparo"},
                )
            ).status_code == 400
            assert (
                await client.patch(
                    f"/api/v1/cozinha/pedidos/{pedido_cancelada.id}/status",
                    headers=headers,
                    json={"status": "em_preparo"},
                )
            ).status_code == 400

            # Em 'pendente': rejeita mesmo status e pulos
            for invalido in ("pendente", "pronto", "entregue"):
                res_err = await client.patch(url, headers=headers, json={"status": invalido})
                assert res_err.status_code == 400

            # Transição válida 1: pendente -> em_preparo
            res_1 = await client.patch(url, headers=headers, json={"status": "em_preparo"})
            assert res_1.status_code == 200
            assert res_1.json()["status"] == "em_preparo"

            # Em 'em_preparo': rejeita retrocesso, mesmo status e pulo
            for invalido in ("pendente", "em_preparo", "entregue"):
                res_err = await client.patch(url, headers=headers, json={"status": invalido})
                assert res_err.status_code == 400

            # Item continua visível na fila enquanto em_preparo
            fila_preparo = await client.get("/api/v1/cozinha/pedidos", headers=headers)
            assert [p["id"] for p in fila_preparo.json()] == [str(pedido.id)]

            # Transição válida 2: em_preparo -> pronto
            res_2 = await client.patch(url, headers=headers, json={"status": "pronto"})
            assert res_2.status_code == 200
            assert res_2.json()["status"] == "pronto"

            # Ao atingir 'pronto', pedido sai da fila ativa da cozinha
            fila_apos_pronto = await client.get("/api/v1/cozinha/pedidos", headers=headers)
            assert fila_apos_pronto.json() == []

            # Em 'pronto': rejeita retrocessos e mesmo status
            for invalido in ("pendente", "em_preparo", "pronto"):
                res_err = await client.patch(url, headers=headers, json={"status": invalido})
                assert res_err.status_code == 400

            # Transição válida 3: pronto -> entregue
            res_3 = await client.patch(url, headers=headers, json={"status": "entregue"})
            assert res_3.status_code == 200
            assert res_3.json()["status"] == "entregue"

            # Estado terminal 'entregue': qualquer transição é rejeitada com 400
            for invalido in ("pendente", "em_preparo", "pronto", "entregue"):
                res_err = await client.patch(url, headers=headers, json={"status": invalido})
                assert res_err.status_code == 400

            # Validação de schema: extra="forbid" e status desconhecido -> 422
            assert (
                await client.patch(
                    url,
                    headers=headers,
                    json={"status": "pendente", "extra_field": "x"},
                )
            ).status_code == 422
            assert (
                await client.patch(
                    url,
                    headers=headers,
                    json={"status": "cancelado"},
                )
            ).status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_kds_rbac_idor_e_dono_multiplos_restaurantes(db_session: AsyncSession):
    cenario = await _criar_cenario_kds(db_session)
    rest_repo = RestauranteRepository(db_session)
    rest_a2 = await rest_repo.create(
        dono_id=cenario["dono_a"].id,
        nome="Restaurante Alpha 2",
        slug="kds-alpha-2",
        codigo_garcom="555555",
        codigo_cozinha="666666",
    )
    await db_session.commit()

    pedido_a = await _criar_item_comanda(
        db_session,
        comanda_id=cenario["comanda_mesa_a"].id,
        item_id=cenario["item_a1"].id,
        nome_item="Filé Parmegiana",
        status_item="pendente",
    )

    token_dono_a = create_access_token(
        {"sub": str(cenario["dono_a"].id), "email": cenario["dono_a"].email, "role": "dono"}
    )
    token_dono_b = create_access_token(
        {"sub": str(cenario["dono_b"].id), "email": cenario["dono_b"].email, "role": "dono"}
    )
    token_garcom_a = create_operational_token(
        cenario["rest_a1"].id,
        "garcom",
        cenario["rest_a1"].codigo_garcom,
    )
    token_cozinha_a = create_operational_token(
        cenario["rest_a1"].id,
        "cozinha",
        cenario["rest_a1"].codigo_cozinha,
    )
    token_cozinha_b = create_operational_token(
        cenario["rest_b"].id,
        "cozinha",
        cenario["rest_b"].codigo_cozinha,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            url_patch = f"/api/v1/cozinha/pedidos/{pedido_a.id}/status"

            # Sem autenticação -> 401/403
            assert (await client.get("/api/v1/cozinha/pedidos")).status_code in (401, 403)
            assert (await client.patch(url_patch, json={"status": "em_preparo"})).status_code in (
                401,
                403,
            )

            # Garçom bloqueado com 403 em ambos os endpoints
            headers_garcom = {"Authorization": f"Bearer {token_garcom_a}"}
            assert (await client.get("/api/v1/cozinha/pedidos", headers=headers_garcom)).status_code == 403
            assert (
                await client.patch(url_patch, headers=headers_garcom, json={"status": "em_preparo"})
            ).status_code == 403

            # Dono A com múltiplos restaurantes exige ?restaurante_id= -> 400 sem param
            headers_dono_a = {"Authorization": f"Bearer {token_dono_a}"}
            assert (await client.get("/api/v1/cozinha/pedidos", headers=headers_dono_a)).status_code == 400
            assert (
                await client.patch(url_patch, headers=headers_dono_a, json={"status": "em_preparo"})
            ).status_code == 400

            # Dono A com restaurante estrangeiro -> 403
            assert (
                await client.get(
                    "/api/v1/cozinha/pedidos",
                    headers=headers_dono_a,
                    params={"restaurante_id": str(cenario["rest_b"].id)},
                )
            ).status_code == 403

            # Dono A com restaurante válido (rest_a2 sem pedidos) -> 200 []
            res_a2 = await client.get(
                "/api/v1/cozinha/pedidos",
                headers=headers_dono_a,
                params={"restaurante_id": str(rest_a2.id)},
            )
            assert res_a2.status_code == 200
            assert res_a2.json() == []

            # Dono A com rest_a1 -> 200 em GET e PATCH
            res_a1 = await client.get(
                "/api/v1/cozinha/pedidos",
                headers=headers_dono_a,
                params={"restaurante_id": str(cenario["rest_a1"].id)},
            )
            assert res_a1.status_code == 200
            assert len(res_a1.json()) == 1

            # Cross-tenant IDOR: cozinha_a informando ?restaurante_id=rest_b -> 403
            headers_cozinha_a = {"Authorization": f"Bearer {token_cozinha_a}"}
            assert (
                await client.get(
                    "/api/v1/cozinha/pedidos",
                    headers=headers_cozinha_a,
                    params={"restaurante_id": str(cenario["rest_b"].id)},
                )
            ).status_code == 403

            # Cross-tenant IDOR: cozinha_b e dono_b tentando PATCH em pedido de rest_a1 -> 404
            headers_cozinha_b = {"Authorization": f"Bearer {token_cozinha_b}"}
            headers_dono_b = {"Authorization": f"Bearer {token_dono_b}"}
            assert (
                await client.patch(url_patch, headers=headers_cozinha_b, json={"status": "em_preparo"})
            ).status_code == 404
            assert (
                await client.patch(url_patch, headers=headers_dono_b, json={"status": "em_preparo"})
            ).status_code == 404

            # Item inexistente -> 404
            assert (
                await client.patch(
                    f"/api/v1/cozinha/pedidos/{uuid.uuid4()}/status",
                    headers=headers_cozinha_a,
                    json={"status": "em_preparo"},
                )
            ).status_code == 404

            # Dono A avança o pedido com sucesso -> 200
            res_patch_dono = await client.patch(
                url_patch,
                headers=headers_dono_a,
                params={"restaurante_id": str(cenario["rest_a1"].id)},
                json={"status": "em_preparo"},
            )
            assert res_patch_dono.status_code == 200
            assert res_patch_dono.json()["status"] == "em_preparo"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_item_comanda_repository_e_service_carregar_comanda_e_log(
    db_session: AsyncSession,
    caplog: pytest.LogCaptureFixture,
):
    cenario = await _criar_cenario_kds(db_session)
    pedido = await _criar_item_comanda(
        db_session,
        comanda_id=cenario["comanda_mesa_a"].id,
        item_id=cenario["item_a1"].id,
        nome_item="Filé Parmegiana",
        status_item="pendente",
    )

    repo = ItemComandaRepository(db_session)
    carregado = await repo.get_by_id_and_restaurante(
        pedido.id,
        cenario["rest_a1"].id,
        carregar_comanda=True,
    )
    assert carregado is not None
    assert carregado.comanda.identificador == "Mesa 04"

    service = CozinhaService(db_session)
    with caplog.at_level("INFO"):
        atualizado = await service.atualizar_status_pedido(
            restaurante_id=cenario["rest_a1"].id,
            item_comanda_id=pedido.id,
            novo_status="em_preparo",
        )
    assert atualizado.status == "em_preparo"
    assert "de=pendente, para=em_preparo" in caplog.text
