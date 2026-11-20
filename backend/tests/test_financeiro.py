import contextlib
import io
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Date, Numeric
from sqlalchemy.ext.asyncio import AsyncSession

from alembic import command
from src.core.database import Base, get_db
from src.core.security import create_access_token, hash_password
from src.main import app
from src.repositories.comanda import ComandaRepository
from src.repositories.despesa import DespesaRepository
from src.repositories.dono import DonoRepository
from src.repositories.restaurante import RestauranteRepository


async def _criar_cenario_dois_restaurantes(db_session: AsyncSession):
    dono_repo = DonoRepository(db_session)
    restaurante_repo = RestauranteRepository(db_session)

    dono_a = await dono_repo.create(
        nome="Dono Alpha",
        email="fin-alpha@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    restaurante_a = await restaurante_repo.create(
        dono_id=dono_a.id,
        nome="Restaurante Alpha",
        slug="fin-restaurante-alpha",
        codigo_garcom="111111",
        codigo_cozinha="222222",
    )

    dono_b = await dono_repo.create(
        nome="Dono Beta",
        email="fin-beta@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    restaurante_b = await restaurante_repo.create(
        dono_id=dono_b.id,
        nome="Restaurante Beta",
        slug="fin-restaurante-beta",
        codigo_garcom="333333",
        codigo_cozinha="444444",
    )
    await db_session.commit()
    return dono_a, restaurante_a, dono_b, restaurante_b


def _headers_dono(dono) -> dict[str, str]:
    token = create_access_token({"sub": str(dono.id), "email": dono.email, "role": "dono"})
    return {"Authorization": f"Bearer {token}"}


def _headers_operacional(restaurante, role: str) -> dict[str, str]:
    token = create_access_token(
        {"sub": str(restaurante.id), "restaurante_id": str(restaurante.id), "role": role}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_despesa_repository_crud_e_isolamento_multitenant(db_session: AsyncSession):
    _, rest_a, _, rest_b = await _criar_cenario_dois_restaurantes(db_session)
    repo = DespesaRepository(db_session)

    desp_a1 = await repo.create(
        restaurante_id=rest_a.id,
        descricao="  Compra de hortifruti  ",
        categoria="insumos",
        valor=Decimal("150.45"),
        data_pagamento=date(2026, 11, 10),
    )
    desp_a2 = await repo.create(
        restaurante_id=rest_a.id,
        descricao="Conta de Energia",
        categoria="contas_fixas",
        valor=Decimal("320.55"),
        data_pagamento=date(2026, 11, 15),
    )
    desp_b1 = await repo.create(
        restaurante_id=rest_b.id,
        descricao="Manutenção Fogão",
        categoria="manutencao",
        valor=Decimal("900.00"),
        data_pagamento=date(2026, 11, 12),
    )
    await db_session.commit()

    assert desp_a1.descricao == "Compra de hortifruti"
    assert await repo.get_by_id_and_restaurante(desp_a1.id, rest_a.id) is not None
    assert await repo.get_by_id_and_restaurante(desp_a1.id, rest_b.id) is None

    # Listagem isolada por restaurante + ordenação data_pagamento DESC + filtros inclusivos
    lista_a = await repo.list_by_restaurante(rest_a.id)
    assert [d.id for d in lista_a] == [desp_a2.id, desp_a1.id]

    lista_b = await repo.list_by_restaurante(rest_b.id)
    assert [d.id for d in lista_b] == [desp_b1.id]

    filtrada_periodo = await repo.list_by_restaurante(
        rest_a.id,
        data_inicio=date(2026, 11, 10),
        data_fim=date(2026, 11, 10),
    )
    assert [d.id for d in filtrada_periodo] == [desp_a1.id]

    filtrada_cat = await repo.list_by_restaurante(rest_a.id, categoria="contas_fixas")
    assert [d.id for d in filtrada_cat] == [desp_a2.id]

    paginada = await repo.list_by_restaurante(rest_a.id, limit=1, offset=1)
    assert [d.id for d in paginada] == [desp_a1.id]

    # Somas e agrupamentos isolados
    soma_a = await repo.somar_despesas_periodo(
        rest_a.id,
        inicio=date(2026, 11, 10),
        fim=date(2026, 11, 15),
    )
    assert soma_a == Decimal("471.00")
    assert await repo.somar_despesas_periodo(
        rest_a.id,
        inicio=date(2026, 10, 1),
        fim=date(2026, 10, 31),
    ) == Decimal("0.00")

    por_cat_a = await repo.somar_despesas_por_categoria(rest_a.id)
    assert por_cat_a == {
        "insumos": Decimal("150.45"),
        "contas_fixas": Decimal("320.55"),
    }

    # Update cross-tenant falha sem mutar dados
    tentativa_update = await repo.update(
        despesa_id=desp_a1.id,
        restaurante_id=rest_b.id,
        valor=Decimal("1.00"),
    )
    assert tentativa_update is None
    recarregada = await repo.get_by_id_and_restaurante(desp_a1.id, rest_a.id)
    assert recarregada is not None and recarregada.valor == Decimal("150.45")

    # Update legítimo
    atualizada = await repo.update(
        despesa_id=desp_a1.id,
        restaurante_id=rest_a.id,
        descricao="Hortifruti Atualizado",
        categoria="outros",
        atualizar_categoria=True,
        valor=Decimal("180.00"),
        data_pagamento=date(2026, 11, 11),
    )
    await db_session.commit()
    assert atualizada is not None
    assert atualizada.descricao == "Hortifruti Atualizado"
    assert atualizada.categoria == "outros"
    assert atualizada.valor == Decimal("180.00")
    assert atualizada.data_pagamento == date(2026, 11, 11)

    # Delete cross-tenant falha preservando registro
    assert (
        await repo.delete_by_id_and_restaurante(despesa_id=desp_a1.id, restaurante_id=rest_b.id)
        is False
    )
    assert await repo.get_by_id_and_restaurante(desp_a1.id, rest_a.id) is not None

    # Delete legítimo remove apenas a despesa alvo
    assert (
        await repo.delete_by_id_and_restaurante(despesa_id=desp_a1.id, restaurante_id=rest_a.id)
        is True
    )
    await db_session.commit()
    assert await repo.get_by_id_and_restaurante(desp_a1.id, rest_a.id) is None
    assert await repo.get_by_id_and_restaurante(desp_a2.id, rest_a.id) is not None


@pytest.mark.asyncio
async def test_despesas_crud_completo_e_filtros(db_session: AsyncSession):
    dono_a, rest_a, dono_b, rest_b = await _criar_cenario_dois_restaurantes(db_session)
    headers_a = _headers_dono(dono_a)
    headers_b = _headers_dono(dono_b)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # POST criar despesas em Alpha e Beta
            res1 = await client.post(
                "/api/v1/financeiro/despesas",
                headers=headers_a,
                json={
                    "descricao": "  Carne Bovina 20kg  ",
                    "categoria": "insumos",
                    "valor": "850.50",
                    "data_pagamento": "2026-11-05",
                },
            )
            assert res1.status_code == 201
            d1 = res1.json()
            assert d1["restaurante_id"] == str(rest_a.id)
            assert d1["descricao"] == "Carne Bovina 20kg"
            assert d1["categoria"] == "insumos"
            assert Decimal(d1["valor"]) == Decimal("850.50")
            assert d1["data_pagamento"] == "2026-11-05"
            assert "criado_em" in d1

            res2 = await client.post(
                "/api/v1/financeiro/despesas",
                headers=headers_a,
                json={
                    "descricao": "Aluguel Salão",
                    "categoria": "contas_fixas",
                    "valor": "3200.00",
                    "data_pagamento": "2026-11-10",
                },
            )
            assert res2.status_code == 201
            d2 = res2.json()

            res3 = await client.post(
                "/api/v1/financeiro/despesas",
                headers=headers_a,
                json={
                    "descricao": "Troca de Lâmpadas",
                    "categoria": "manutencao",
                    "valor": "95.00",
                    "data_pagamento": "2026-11-20",
                },
            )
            assert res3.status_code == 201
            d3 = res3.json()

            res_b = await client.post(
                "/api/v1/financeiro/despesas",
                headers=headers_b,
                json={
                    "descricao": "Gelo Restaurante Beta",
                    "categoria": "insumos",
                    "valor": "40.00",
                    "data_pagamento": "2026-11-10",
                },
            )
            assert res_b.status_code == 201
            assert res_b.json()["restaurante_id"] == str(rest_b.id)

            # GET lista sem filtro: apenas Alpha, ordenado data_pagamento DESC
            res_list = await client.get("/api/v1/financeiro/despesas", headers=headers_a)
            assert res_list.status_code == 200
            ids = [item["id"] for item in res_list.json()]
            assert ids == [d3["id"], d2["id"], d1["id"]]

            # GET filtros inclusivos por data_inicio e data_fim
            res_periodo = await client.get(
                "/api/v1/financeiro/despesas?data_inicio=2026-11-05&data_fim=2026-11-10",
                headers=headers_a,
            )
            assert res_periodo.status_code == 200
            assert [i["id"] for i in res_periodo.json()] == [d2["id"], d1["id"]]

            # GET filtro por categoria + período combinado
            res_cat = await client.get(
                "/api/v1/financeiro/despesas?categoria=insumos&data_inicio=2026-11-05&data_fim=2026-11-20",
                headers=headers_a,
            )
            assert res_cat.status_code == 200
            assert [i["id"] for i in res_cat.json()] == [d1["id"]]

            # Paginação e limites OWASP (limit <= 100)
            res_pag = await client.get(
                "/api/v1/financeiro/despesas?limit=1&offset=1",
                headers=headers_a,
            )
            assert res_pag.status_code == 200
            assert [i["id"] for i in res_pag.json()] == [d2["id"]]
            assert (
                await client.get("/api/v1/financeiro/despesas?limit=100", headers=headers_a)
            ).status_code == 200
            assert (
                await client.get("/api/v1/financeiro/despesas?limit=101", headers=headers_a)
            ).status_code == 422
            assert (
                await client.get("/api/v1/financeiro/despesas?limit=0", headers=headers_a)
            ).status_code == 422
            assert (
                await client.get("/api/v1/financeiro/despesas?offset=-1", headers=headers_a)
            ).status_code == 422

            # GET /{id} existente vs inexistente
            res_get = await client.get(
                f"/api/v1/financeiro/despesas/{d1['id']}",
                headers=headers_a,
            )
            assert res_get.status_code == 200
            assert res_get.json()["id"] == d1["id"]

            assert (
                await client.get(
                    f"/api/v1/financeiro/despesas/{uuid.uuid4()}",
                    headers=headers_a,
                )
            ).status_code == 404

            # PATCH /{id} parcial preserva campos não enviados
            res_patch = await client.patch(
                f"/api/v1/financeiro/despesas/{d1['id']}",
                headers=headers_a,
                json={"valor": "890.25", "categoria": "outros"},
            )
            assert res_patch.status_code == 200
            patched = res_patch.json()
            assert Decimal(patched["valor"]) == Decimal("890.25")
            assert patched["categoria"] == "outros"
            assert patched["descricao"] == "Carne Bovina 20kg"
            assert patched["data_pagamento"] == "2026-11-05"

            assert (
                await client.patch(
                    f"/api/v1/financeiro/despesas/{uuid.uuid4()}",
                    headers=headers_a,
                    json={"valor": "10.00"},
                )
            ).status_code == 404

            # DELETE /{id} -> 204 e subsequente GET -> 404
            res_del = await client.delete(
                f"/api/v1/financeiro/despesas/{d3['id']}",
                headers=headers_a,
            )
            assert res_del.status_code == 204
            assert res_del.content == b""

            assert (
                await client.get(
                    f"/api/v1/financeiro/despesas/{d3['id']}",
                    headers=headers_a,
                )
            ).status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_financeiro_resumo_fluxo_de_caixa_e_periodo(db_session: AsyncSession):
    dono_a, rest_a, _, rest_b = await _criar_cenario_dois_restaurantes(db_session)
    comanda_repo = ComandaRepository(db_session)
    despesa_repo = DespesaRepository(db_session)

    # Comandas fechadas dentro do período (incluindo início 00:15Z e fim 23:30Z)
    c1 = await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=1)
    await comanda_repo.fechar(
        comanda_id=c1.id,
        restaurante_id=rest_a.id,
        subtotal=Decimal("109.59"),
        taxa_servico=Decimal("10.96"),
        desconto=Decimal("0.00"),
        valor_total=Decimal("120.55"),
        metodo_pagamento="pix",
        fechado_em=datetime(2026, 11, 20, 23, 30, 0, tzinfo=UTC),
    )

    c2 = await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=2)
    await comanda_repo.fechar(
        comanda_id=c2.id,
        restaurante_id=rest_a.id,
        subtotal=Decimal("79.45"),
        taxa_servico=Decimal("0.00"),
        desconto=Decimal("0.00"),
        valor_total=Decimal("79.45"),
        metodo_pagamento="dinheiro",
        fechado_em=datetime(2026, 11, 10, 0, 15, 0, tzinfo=UTC),
    )

    # Comanda fechada fora do período (excluída)
    c_fora = await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=3)
    await comanda_repo.fechar(
        comanda_id=c_fora.id,
        restaurante_id=rest_a.id,
        subtotal=Decimal("500.00"),
        taxa_servico=Decimal("0.00"),
        desconto=Decimal("0.00"),
        valor_total=Decimal("500.00"),
        metodo_pagamento="credito",
        fechado_em=datetime(2026, 11, 21, 0, 0, 1, tzinfo=UTC),
    )

    # Comanda aberta e comanda cancelada (excluídas)
    c_aberta = await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=4)
    await comanda_repo.update_totais(
        comanda_id=c_aberta.id,
        restaurante_id=rest_a.id,
        subtotal=Decimal("999.00"),
        valor_total=Decimal("999.00"),
    )

    c_cancelada = await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=5)
    c_cancelada.status = "cancelada"
    c_cancelada.valor_total = Decimal("888.00")
    c_cancelada.fechado_em = datetime(2026, 11, 15, 12, 0, 0, tzinfo=UTC)

    # Comanda fechada de outro restaurante (excluída)
    c_beta = await comanda_repo.create(restaurante_id=rest_b.id, numero_mesa=1)
    await comanda_repo.fechar(
        comanda_id=c_beta.id,
        restaurante_id=rest_b.id,
        subtotal=Decimal("777.00"),
        taxa_servico=Decimal("0.00"),
        desconto=Decimal("0.00"),
        valor_total=Decimal("777.00"),
        metodo_pagamento="pix",
        fechado_em=datetime(2026, 11, 15, 12, 0, 0, tzinfo=UTC),
    )

    # Despesas Alpha dentro e fora do período + despesa Beta dentro do período
    await despesa_repo.create(
        restaurante_id=rest_a.id,
        descricao="Insumos período",
        categoria="insumos",
        valor=Decimal("45.10"),
        data_pagamento=date(2026, 11, 10),
    )
    await despesa_repo.create(
        restaurante_id=rest_a.id,
        descricao="Água período",
        categoria="contas_fixas",
        valor=Decimal("30.20"),
        data_pagamento=date(2026, 11, 20),
    )
    await despesa_repo.create(
        restaurante_id=rest_a.id,
        descricao="Despesa fora",
        categoria="outros",
        valor=Decimal("200.00"),
        data_pagamento=date(2026, 11, 21),
    )
    await despesa_repo.create(
        restaurante_id=rest_b.id,
        descricao="Despesa Beta",
        categoria="insumos",
        valor=Decimal("300.00"),
        data_pagamento=date(2026, 11, 15),
    )
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers_a = _headers_dono(dono_a)

            res = await client.get(
                "/api/v1/financeiro/resumo?data_inicio=2026-11-10&data_fim=2026-11-20",
                headers=headers_a,
            )
            assert res.status_code == 200
            body = res.json()
            assert body["restaurante_id"] == str(rest_a.id)
            assert body["data_inicio"] == "2026-11-10"
            assert body["data_fim"] == "2026-11-20"
            assert body["total_vendas"] == "200.00"
            assert body["total_despesas"] == "75.30"
            assert body["saldo"] == "124.70"
            assert body["despesas_por_categoria"] == {
                "insumos": "45.10",
                "contas_fixas": "30.20",
                "manutencao": "0.00",
                "outros": "0.00",
            }

            # Saldo negativo quando despesas superam vendas (ex: 2026-11-21)
            # No dia 21: vendas = 500.00, se adicionarmos despesa de 650.00 no mesmo dia -> saldo = -150.00
            await despesa_repo.create(
                restaurante_id=rest_a.id,
                descricao="Reforma Extra",
                categoria="manutencao",
                valor=Decimal("650.00"),
                data_pagamento=date(2026, 11, 21),
            )
            await db_session.commit()

            res_neg = await client.get(
                "/api/v1/financeiro/resumo?data_inicio=2026-11-21&data_fim=2026-11-21",
                headers=headers_a,
            )
            assert res_neg.status_code == 200
            body_neg = res_neg.json()
            assert body_neg["total_vendas"] == "500.00"
            assert body_neg["total_despesas"] == "850.00"
            assert body_neg["saldo"] == "-350.00"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_financeiro_resumo_periodo_vazio_e_precisao_decimal(db_session: AsyncSession):
    dono_a, rest_a, _, _ = await _criar_cenario_dois_restaurantes(db_session)
    comanda_repo = ComandaRepository(db_session)
    despesa_repo = DespesaRepository(db_session)

    # Valores clássicos de armadilha IEEE-754 (0.10 + 0.20 e 19.99 + 0.01)
    c1 = await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=1)
    await comanda_repo.fechar(
        comanda_id=c1.id,
        restaurante_id=rest_a.id,
        subtotal=Decimal("10.10"),
        taxa_servico=Decimal("0.00"),
        desconto=Decimal("0.00"),
        valor_total=Decimal("10.10"),
        metodo_pagamento="pix",
        fechado_em=datetime(2026, 12, 1, 14, 0, 0, tzinfo=UTC),
    )
    await despesa_repo.create(
        restaurante_id=rest_a.id,
        descricao="Item 0.10",
        categoria="outros",
        valor=Decimal("0.10"),
        data_pagamento=date(2026, 12, 1),
    )
    await despesa_repo.create(
        restaurante_id=rest_a.id,
        descricao="Item 0.20",
        categoria="outros",
        valor=Decimal("0.20"),
        data_pagamento=date(2026, 12, 1),
    )
    await despesa_repo.create(
        restaurante_id=rest_a.id,
        descricao="Item 9.70",
        categoria="insumos",
        valor=Decimal("9.70"),
        data_pagamento=date(2026, 12, 1),
    )
    await db_session.commit()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers_a = _headers_dono(dono_a)

            # Período totalmente vazio -> "0.00"
            res_vazio = await client.get(
                "/api/v1/financeiro/resumo?data_inicio=2026-01-01&data_fim=2026-01-31",
                headers=headers_a,
            )
            assert res_vazio.status_code == 200
            vazio = res_vazio.json()
            assert vazio["total_vendas"] == "0.00"
            assert vazio["total_despesas"] == "0.00"
            assert vazio["saldo"] == "0.00"

            # Precisão decimal exata em dia único (10.10 - (0.10 + 0.20 + 9.70) = 0.10)
            res_prec = await client.get(
                "/api/v1/financeiro/resumo?data_inicio=2026-12-01&data_fim=2026-12-01",
                headers=headers_a,
            )
            assert res_prec.status_code == 200
            prec = res_prec.json()
            assert prec["total_vendas"] == "10.10"
            assert prec["total_despesas"] == "10.00"
            assert prec["saldo"] == "0.10"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_despesas_e_resumo_validacoes_schema_e_edge_cases(db_session: AsyncSession):
    dono_a, _, _, rest_b = await _criar_cenario_dois_restaurantes(db_session)
    headers_a = _headers_dono(dono_a)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Período invertido (data_inicio > data_fim) -> 400
            assert (
                await client.get(
                    "/api/v1/financeiro/resumo?data_inicio=2026-11-20&data_fim=2026-11-10",
                    headers=headers_a,
                )
            ).status_code == 400
            assert (
                await client.get(
                    "/api/v1/financeiro/despesas?data_inicio=2026-11-20&data_fim=2026-11-10",
                    headers=headers_a,
                )
            ).status_code == 400

            # Categoria inválida em POST / GET filter
            assert (
                await client.post(
                    "/api/v1/financeiro/despesas",
                    headers=headers_a,
                    json={
                        "descricao": "Anúncio",
                        "categoria": "marketing",
                        "valor": "50.00",
                        "data_pagamento": "2026-11-20",
                    },
                )
            ).status_code == 422
            assert (
                await client.get(
                    "/api/v1/financeiro/despesas?categoria=marketing",
                    headers=headers_a,
                )
            ).status_code == 422

            # Valores <= 0 ou > 2 casas decimais
            for bad_valor in ("0", "0.00", "-10.00", "10.125"):
                assert (
                    await client.post(
                        "/api/v1/financeiro/despesas",
                        headers=headers_a,
                        json={
                            "descricao": "Despesa Teste",
                            "categoria": "outros",
                            "valor": bad_valor,
                            "data_pagamento": "2026-11-20",
                        },
                    )
                ).status_code == 422

            # Descrição em branco / curta / longa
            for bad_desc in ("   ", "A", "X" * 201):
                assert (
                    await client.post(
                        "/api/v1/financeiro/despesas",
                        headers=headers_a,
                        json={
                            "descricao": bad_desc,
                            "categoria": "outros",
                            "valor": "10.00",
                            "data_pagamento": "2026-11-20",
                        },
                    )
                ).status_code == 422

            # extra="forbid" no POST (tentativa de mass assignment com restaurante_id)
            assert (
                await client.post(
                    "/api/v1/financeiro/despesas",
                    headers=headers_a,
                    json={
                        "descricao": "Gelo",
                        "categoria": "insumos",
                        "valor": "15.00",
                        "data_pagamento": "2026-11-20",
                        "restaurante_id": str(rest_b.id),
                    },
                )
            ).status_code == 422

            # Criar despesa válida para testar validações do PATCH
            created = await client.post(
                "/api/v1/financeiro/despesas",
                headers=headers_a,
                json={
                    "descricao": "Despesa Válida",
                    "categoria": "outros",
                    "valor": "25.00",
                    "data_pagamento": "2026-11-20",
                },
            )
            assert created.status_code == 201
            desp_id = created.json()["id"]

            # PATCH com campo extra desconhecido, null explícito, body vazio ou categoria inválida -> 422
            for bad_patch in (
                {"valor": "30.00", "campo_desconhecido": 1},
                {"valor": None},
                {"descricao": None},
                {"categoria": None},
                {"data_pagamento": None},
                {},
                {"categoria": "invalida"},
            ):
                assert (
                    await client.patch(
                        f"/api/v1/financeiro/despesas/{desp_id}",
                        headers=headers_a,
                        json=bad_patch,
                    )
                ).status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_financeiro_rbac_bloqueia_garcom_cozinha_e_nao_autenticado(db_session: AsyncSession):
    dono_a, rest_a, _, _ = await _criar_cenario_dois_restaurantes(db_session)
    despesa_repo = DespesaRepository(db_session)
    desp_a = await despesa_repo.create(
        restaurante_id=rest_a.id,
        descricao="Despesa Protegida",
        categoria="outros",
        valor=Decimal("50.00"),
        data_pagamento=date(2026, 11, 20),
    )
    await db_session.commit()

    headers_garcom = _headers_operacional(rest_a, "garcom")
    headers_cozinha = _headers_operacional(rest_a, "cozinha")
    headers_invalido = {"Authorization": "Bearer token.invalido.aqui"}
    _ = dono_a

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            payload = {
                "descricao": "Tentativa",
                "categoria": "outros",
                "valor": "10.00",
                "data_pagamento": "2026-11-20",
            }
            endpoints = [
                ("POST", "/api/v1/financeiro/despesas", payload),
                ("GET", "/api/v1/financeiro/despesas", None),
                ("GET", f"/api/v1/financeiro/despesas/{desp_a.id}", None),
                ("PATCH", f"/api/v1/financeiro/despesas/{desp_a.id}", {"valor": "12.00"}),
                ("DELETE", f"/api/v1/financeiro/despesas/{desp_a.id}", None),
                ("GET", "/api/v1/financeiro/resumo", None),
            ]

            for method, url, body in endpoints:
                # Sem autenticação -> 401/403
                res_anon = await client.request(method, url, json=body)
                assert res_anon.status_code in (401, 403)

                # Token inválido -> 401
                res_inv = await client.request(method, url, headers=headers_invalido, json=body)
                assert res_inv.status_code == 401

                # Garçom -> 403
                res_garcom = await client.request(method, url, headers=headers_garcom, json=body)
                assert res_garcom.status_code == 403

                # Cozinha -> 403
                res_cozinha = await client.request(method, url, headers=headers_cozinha, json=body)
                assert res_cozinha.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_financeiro_idor_e_multiplos_restaurantes(db_session: AsyncSession):
    dono_a, rest_a, dono_b, _ = await _criar_cenario_dois_restaurantes(db_session)
    restaurante_repo = RestauranteRepository(db_session)
    despesa_repo = DespesaRepository(db_session)

    rest_a2 = await restaurante_repo.create(
        dono_id=dono_a.id,
        nome="Restaurante Alpha Filial",
        slug="fin-restaurante-alpha-2",
        codigo_garcom="555555",
        codigo_cozinha="666666",
    )
    desp_a1 = await despesa_repo.create(
        restaurante_id=rest_a.id,
        descricao="Despesa Matriz",
        categoria="insumos",
        valor=Decimal("100.00"),
        data_pagamento=date(2026, 11, 20),
    )
    desp_a2 = await despesa_repo.create(
        restaurante_id=rest_a2.id,
        descricao="Despesa Filial",
        categoria="manutencao",
        valor=Decimal("250.00"),
        data_pagamento=date(2026, 11, 20),
    )
    await db_session.commit()

    headers_a = _headers_dono(dono_a)
    headers_b = _headers_dono(dono_b)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # IDOR por entity ID -> 404 para Dono B
            assert (
                await client.get(
                    f"/api/v1/financeiro/despesas/{desp_a1.id}",
                    headers=headers_b,
                )
            ).status_code == 404
            assert (
                await client.patch(
                    f"/api/v1/financeiro/despesas/{desp_a1.id}",
                    headers=headers_b,
                    json={"valor": "1.00"},
                )
            ).status_code == 404
            assert (
                await client.delete(
                    f"/api/v1/financeiro/despesas/{desp_a1.id}",
                    headers=headers_b,
                )
            ).status_code == 404

            # IDOR via ?restaurante_id={rest_a.id} -> 403 para Dono B em todas as rotas
            assert (
                await client.post(
                    f"/api/v1/financeiro/despesas?restaurante_id={rest_a.id}",
                    headers=headers_b,
                    json={
                        "descricao": "Invasão",
                        "categoria": "outros",
                        "valor": "10.00",
                        "data_pagamento": "2026-11-20",
                    },
                )
            ).status_code == 403
            assert (
                await client.get(
                    f"/api/v1/financeiro/despesas?restaurante_id={rest_a.id}",
                    headers=headers_b,
                )
            ).status_code == 403
            assert (
                await client.get(
                    f"/api/v1/financeiro/resumo?restaurante_id={rest_a.id}",
                    headers=headers_b,
                )
            ).status_code == 403
            assert (
                await client.get(
                    f"/api/v1/financeiro/despesas/{desp_a1.id}?restaurante_id={rest_a.id}",
                    headers=headers_b,
                )
            ).status_code == 403

            # Dono A com múltiplos restaurantes sem ?restaurante_id -> 400
            assert (
                await client.get("/api/v1/financeiro/despesas", headers=headers_a)
            ).status_code == 400
            assert (
                await client.get("/api/v1/financeiro/resumo", headers=headers_a)
            ).status_code == 400

            # Dono A especificando ?restaurante_id={rest_a2.id} isola despesas e resumo na filial
            res_filial = await client.get(
                f"/api/v1/financeiro/despesas?restaurante_id={rest_a2.id}",
                headers=headers_a,
            )
            assert res_filial.status_code == 200
            assert [d["id"] for d in res_filial.json()] == [str(desp_a2.id)]

            res_resumo_filial = await client.get(
                f"/api/v1/financeiro/resumo?restaurante_id={rest_a2.id}",
                headers=headers_a,
            )
            assert res_resumo_filial.status_code == 200
            assert res_resumo_filial.json()["restaurante_id"] == str(rest_a2.id)
            assert res_resumo_filial.json()["total_despesas"] == "250.00"
            assert res_resumo_filial.json()["saldo"] == "-250.00"
    finally:
        app.dependency_overrides.clear()


def test_alembic_migration_0004_estrutura_e_cadeia():
    backend_dir = Path(__file__).resolve().parents[1]
    cfg = Config(str(backend_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))

    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert len(heads) == 1
    head_rev = heads[0]
    assert head_rev == "0004_criar_tabela_despesa"

    rev_obj = script.get_revision(head_rev)
    assert rev_obj is not None
    assert rev_obj.down_revision == "0003_comanda_item_comanda"

    # Verifica tabela e colunas no Base.metadata
    assert "despesa" in Base.metadata.tables
    despesa_table = Base.metadata.tables["despesa"]
    expected_cols = {
        "id",
        "restaurante_id",
        "descricao",
        "categoria",
        "valor",
        "data_pagamento",
        "criado_em",
    }
    assert expected_cols.issubset(set(despesa_table.columns.keys()))
    assert isinstance(despesa_table.c.valor.type, Numeric)
    assert despesa_table.c.valor.type.precision == 10
    assert despesa_table.c.valor.type.scale == 2
    assert isinstance(despesa_table.c.data_pagamento.type, Date)
    fk_targets = {fk.target_fullname for fk in despesa_table.c.restaurante_id.foreign_keys}
    assert "restaurante.id" in fk_targets
    index_names = {idx.name for idx in despesa_table.indexes}
    assert {
        "ix_despesa_restaurante_id",
        "ix_despesa_restaurante_data",
        "ix_despesa_restaurante_categoria",
    }.issubset(index_names)

    # Verifica geração offline de DDL PostgreSQL para upgrade e downgrade
    up_buf = io.StringIO()
    cfg_up = Config(str(backend_dir / "alembic.ini"))
    cfg_up.set_main_option("script_location", str(backend_dir / "alembic"))
    with contextlib.redirect_stdout(up_buf):
        command.upgrade(cfg_up, "head", sql=True)
    up_sql = up_buf.getvalue()
    assert "CREATE TABLE despesa" in up_sql
    assert "ix_despesa_restaurante_id" in up_sql
    assert "ix_despesa_restaurante_data" in up_sql
    assert "ix_despesa_restaurante_categoria" in up_sql

    down_buf = io.StringIO()
    cfg_down = Config(str(backend_dir / "alembic.ini"))
    cfg_down.set_main_option("script_location", str(backend_dir / "alembic"))
    with contextlib.redirect_stdout(down_buf):
        command.downgrade(cfg_down, f"{head_rev}:0003_comanda_item_comanda", sql=True)
    down_sql = down_buf.getvalue()
    assert "DROP TABLE despesa" in down_sql
