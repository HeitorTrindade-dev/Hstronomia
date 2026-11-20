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
from src.repositories.dono import DonoRepository
from src.repositories.item import ItemRepository
from src.repositories.restaurante import RestauranteRepository


async def _criar_cenario_comandas(db_session: AsyncSession):
    dono_repo = DonoRepository(db_session)
    rest_repo = RestauranteRepository(db_session)
    item_repo = ItemRepository(db_session)

    dono_a = await dono_repo.create(
        nome="Dono Listagem A",
        email="listagem_a@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    rest_a = await rest_repo.create(
        dono_id=dono_a.id,
        nome="Restaurante Listagem A",
        slug="rest-listagem-a",
        codigo_garcom="111111",
        codigo_cozinha="222222",
    )
    prato_a = await item_repo.create(
        restaurante_id=rest_a.id,
        nome="Moqueca Baiana",
        descricao="Acompanha pirão e arroz",
        preco=Decimal("89.90"),
    )

    dono_b = await dono_repo.create(
        nome="Dono Listagem B",
        email="listagem_b@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    rest_b = await rest_repo.create(
        dono_id=dono_b.id,
        nome="Restaurante Listagem B",
        slug="rest-listagem-b",
        codigo_garcom="333333",
        codigo_cozinha="444444",
    )
    await db_session.commit()
    return dono_a, rest_a, prato_a, dono_b, rest_b


@pytest.mark.asyncio
async def test_listagem_detalhamento_e_cancelamento_comandas_fluxo_completo(
    db_session: AsyncSession,
):
    dono_a, rest_a, prato_a, _, _ = await _criar_cenario_comandas(db_session)
    token_garcom = create_operational_token(rest_a.id, "garcom", rest_a.codigo_garcom)
    token_dono = create_access_token(
        {"sub": str(dono_a.id), "email": dono_a.email, "role": "dono"}
    )
    token_cozinha = create_operational_token(rest_a.id, "cozinha", rest_a.codigo_cozinha)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers_garcom = {"Authorization": f"Bearer {token_garcom}"}
            headers_dono = {"Authorization": f"Bearer {token_dono}"}
            headers_cozinha = {"Authorization": f"Bearer {token_cozinha}"}

            # 1. Abre duas comandas (Mesa 10 e Balcão)
            comanda_mesa = (
                await client.post(
                    "/api/v1/comandas",
                    headers=headers_garcom,
                    json={"numero_mesa": 10, "identificador": "Mesa 10", "tipo_atendimento": "mesa"},
                )
            ).json()
            comanda_balcao = (
                await client.post(
                    "/api/v1/comandas",
                    headers=headers_garcom,
                    json={"identificador": "Balcão - Carlos", "tipo_atendimento": "balcao"},
                )
            ).json()

            # Adiciona item à comanda da Mesa 10
            await client.post(
                f"/api/v1/comandas/{comanda_mesa['id']}/itens",
                headers=headers_garcom,
                json={"item_id": str(prato_a.id), "quantidade": 2, "observacao": "Sem coentro"},
            )

            # 2. Detalhamento da comanda (GET /api/v1/comandas/{id}) retorna comanda + itens congelados
            res_detalhe = await client.get(
                f"/api/v1/comandas/{comanda_mesa['id']}",
                headers=headers_garcom,
            )
            assert res_detalhe.status_code == 200
            detalhe = res_detalhe.json()
            assert detalhe["id"] == comanda_mesa["id"]
            assert Decimal(detalhe["subtotal"]) == Decimal("179.80")
            assert len(detalhe["itens"]) == 1
            assert detalhe["itens"][0]["nome_item"] == "Moqueca Baiana"
            assert Decimal(detalhe["itens"][0]["preco_unitario"]) == Decimal("89.90")
            assert detalhe["itens"][0]["observacao"] == "Sem coentro"

            # 3. Listagem de comandas (GET /api/v1/comandas) com filtros de status e tipo_atendimento
            res_todas = await client.get("/api/v1/comandas", headers=headers_garcom)
            assert res_todas.status_code == 200
            assert len(res_todas.json()) == 2

            res_balcao = await client.get(
                "/api/v1/comandas?status=aberta&tipo_atendimento=balcao",
                headers=headers_garcom,
            )
            assert res_balcao.status_code == 200
            assert [c["id"] for c in res_balcao.json()] == [comanda_balcao["id"]]

            # 4. Cancelamento da comanda da Mesa 10 (POST /api/v1/comandas/{id}/cancelar)
            res_cancelar = await client.post(
                f"/api/v1/comandas/{comanda_mesa['id']}/cancelar",
                headers=headers_garcom,
            )
            assert res_cancelar.status_code == 200
            cancelada = res_cancelar.json()
            assert cancelada["status"] == "cancelada"
            assert cancelada["fechado_em"] is not None

            # Não permite cancelar novamente nem fechar uma comanda já cancelada -> 400
            assert (
                await client.post(
                    f"/api/v1/comandas/{comanda_mesa['id']}/cancelar",
                    headers=headers_garcom,
                )
            ).status_code == 400
            assert (
                await client.post(
                    f"/api/v1/comandas/{comanda_mesa['id']}/fechar",
                    headers=headers_garcom,
                    json={"metodo_pagamento": "pix"},
                )
            ).status_code == 400

            # 5. Mesa 10 foi liberada para nova comanda aberta
            res_nova_mesa_10 = await client.post(
                "/api/v1/comandas",
                headers=headers_garcom,
                json={"numero_mesa": 10, "identificador": "Mesa 10 - Novo Cliente"},
            )
            assert res_nova_mesa_10.status_code == 201

            # 6. Pedido da comanda cancelada saiu da fila KDS e NÃO soma no faturamento financeiro
            res_kds = await client.get("/api/v1/cozinha/pedidos", headers=headers_cozinha)
            assert res_kds.status_code == 200
            assert res_kds.json() == []

            res_resumo = await client.get("/api/v1/financeiro/resumo", headers=headers_dono)
            assert res_resumo.status_code == 200
            assert Decimal(res_resumo.json()["total_vendas"]) == Decimal("0.00")

            # Filtro por status=cancelada retorna apenas a comanda cancelada
            res_canceladas = await client.get(
                "/api/v1/comandas?status=cancelada",
                headers=headers_dono,
            )
            assert res_canceladas.status_code == 200
            assert [c["id"] for c in res_canceladas.json()] == [comanda_mesa["id"]]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_listagem_detalhamento_cancelamento_rbac_e_idor(
    db_session: AsyncSession,
):
    dono_a, rest_a, _, dono_b, _ = await _criar_cenario_comandas(db_session)
    token_dono_a = create_access_token(
        {"sub": str(dono_a.id), "email": dono_a.email, "role": "dono"}
    )
    token_dono_b = create_access_token(
        {"sub": str(dono_b.id), "email": dono_b.email, "role": "dono"}
    )
    token_cozinha_a = create_operational_token(rest_a.id, "cozinha", rest_a.codigo_cozinha)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers_a = {"Authorization": f"Bearer {token_dono_a}"}
            headers_b = {"Authorization": f"Bearer {token_dono_b}"}
            headers_cozinha = {"Authorization": f"Bearer {token_cozinha_a}"}

            comanda_a = (
                await client.post(
                    "/api/v1/comandas",
                    headers=headers_a,
                    json={"numero_mesa": 1, "identificador": "Mesa 01"},
                )
            ).json()

            # 1. BFLA: Cozinha bloqueada nas rotas de gestão de comanda -> 403
            assert (
                await client.get("/api/v1/comandas", headers=headers_cozinha)
            ).status_code == 403
            assert (
                await client.get(f"/api/v1/comandas/{comanda_a['id']}", headers=headers_cozinha)
            ).status_code == 403
            assert (
                await client.post(
                    f"/api/v1/comandas/{comanda_a['id']}/cancelar",
                    headers=headers_cozinha,
                )
            ).status_code == 403

            # 2. IDOR: Dono B não vê nem cancela comanda do Restaurante A
            res_list_b = await client.get("/api/v1/comandas", headers=headers_b)
            assert res_list_b.status_code == 200
            assert res_list_b.json() == []

            assert (
                await client.get(f"/api/v1/comandas/{comanda_a['id']}", headers=headers_b)
            ).status_code == 404
            assert (
                await client.post(
                    f"/api/v1/comandas/{comanda_a['id']}/cancelar",
                    headers=headers_b,
                )
            ).status_code == 404
    finally:
        app.dependency_overrides.clear()
