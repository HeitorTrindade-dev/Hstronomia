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


async def _criar_cenario_fechamento(db_session: AsyncSession):
    dono_repo = DonoRepository(db_session)
    rest_repo = RestauranteRepository(db_session)
    item_repo = ItemRepository(db_session)

    dono_a = await dono_repo.create(
        nome="Dono Fechamento A",
        email="fechamento_a@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    rest_a = await rest_repo.create(
        dono_id=dono_a.id,
        nome="Restaurante Fechamento A",
        slug="rest-fechamento-a",
        codigo_garcom="111111",
        codigo_cozinha="222222",
    )
    prato = await item_repo.create(
        restaurante_id=rest_a.id,
        nome="Risoto de Funghi",
        descricao="Arroz arbóreo e cogumelos",
        preco=Decimal("55.25"),
    )
    bebida = await item_repo.create(
        restaurante_id=rest_a.id,
        nome="Suco de Uva Integral",
        descricao="Taça 300ml",
        preco=Decimal("14.50"),
    )

    dono_b = await dono_repo.create(
        nome="Dono Fechamento B",
        email="fechamento_b@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    rest_b = await rest_repo.create(
        dono_id=dono_b.id,
        nome="Restaurante Fechamento B",
        slug="rest-fechamento-b",
        codigo_garcom="333333",
        codigo_cozinha="444444",
    )
    await db_session.commit()
    return dono_a, rest_a, prato, bebida, dono_b, rest_b


@pytest.mark.asyncio
async def test_previa_e_fechamento_comanda_calculos_10_porcento_e_desconto(
    db_session: AsyncSession,
):
    dono_a, rest_a, prato, bebida, _, _ = await _criar_cenario_fechamento(db_session)
    token_garcom = create_operational_token(rest_a.id, "garcom", rest_a.codigo_garcom)
    token_dono = create_access_token(
        {"sub": str(dono_a.id), "email": dono_a.email, "role": "dono"}
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers_garcom = {"Authorization": f"Bearer {token_garcom}"}
            headers_dono = {"Authorization": f"Bearer {token_dono}"}

            # 1. Abre comanda na Mesa 07 e adiciona itens: 2x 55.25 (110.50) + 1x 14.50 = 125.00
            comanda = (
                await client.post(
                    "/api/v1/comandas",
                    headers=headers_garcom,
                    json={"numero_mesa": 7, "identificador": "Mesa 07", "tipo_atendimento": "mesa"},
                )
            ).json()
            comanda_id = comanda["id"]

            await client.post(
                f"/api/v1/comandas/{comanda_id}/itens",
                headers=headers_garcom,
                json={"item_id": str(prato.id), "quantidade": 2},
            )
            await client.post(
                f"/api/v1/comandas/{comanda_id}/itens",
                headers=headers_garcom,
                json={"item_id": str(bebida.id), "quantidade": 1},
            )

            # 2. Prévia padrão (com 10% taxa de serviço e sem desconto)
            res_previa_padrao = await client.get(
                f"/api/v1/comandas/{comanda_id}/previa",
                headers=headers_garcom,
            )
            assert res_previa_padrao.status_code == 200
            previa_padrao = res_previa_padrao.json()
            assert len(previa_padrao["itens"]) == 2
            assert Decimal(previa_padrao["subtotal"]) == Decimal("125.00")
            assert previa_padrao["incluir_taxa_servico"] is True
            assert Decimal(previa_padrao["taxa_servico"]) == Decimal("12.50")
            assert Decimal(previa_padrao["desconto"]) == Decimal("0.00")
            assert Decimal(previa_padrao["valor_total"]) == Decimal("137.50")

            # 3. Prévia sem 10% e com desconto de R$ 15.00
            res_previa_sem_taxa = await client.get(
                f"/api/v1/comandas/{comanda_id}/previa?incluir_taxa_servico=false&desconto=15.00",
                headers=headers_garcom,
            )
            assert res_previa_sem_taxa.status_code == 200
            previa_sem_taxa = res_previa_sem_taxa.json()
            assert Decimal(previa_sem_taxa["subtotal"]) == Decimal("125.00")
            assert Decimal(previa_sem_taxa["taxa_servico"]) == Decimal("0.00")
            assert Decimal(previa_sem_taxa["desconto"]) == Decimal("15.00")
            assert Decimal(previa_sem_taxa["valor_total"]) == Decimal("110.00")

            # 4. Prévia com desconto maior que o valor bruto -> 400
            res_desconto_excessivo = await client.get(
                f"/api/v1/comandas/{comanda_id}/previa?incluir_taxa_servico=false&desconto=125.01",
                headers=headers_garcom,
            )
            assert res_desconto_excessivo.status_code == 400

            # 5. Fechamento da comanda com 10% (12.50) e desconto de 7.50 -> total 130.00 no PIX
            res_fechar = await client.post(
                f"/api/v1/comandas/{comanda_id}/fechar",
                headers=headers_garcom,
                json={
                    "metodo_pagamento": "pix",
                    "incluir_taxa_servico": True,
                    "desconto": "7.50",
                },
            )
            assert res_fechar.status_code == 200
            fechada = res_fechar.json()
            assert fechada["status"] == "fechada"
            assert fechada["metodo_pagamento"] == "pix"
            assert fechada["fechado_em"] is not None
            assert Decimal(fechada["subtotal"]) == Decimal("125.00")
            assert Decimal(fechada["taxa_servico"]) == Decimal("12.50")
            assert Decimal(fechada["desconto"]) == Decimal("7.50")
            assert Decimal(fechada["valor_total"]) == Decimal("130.00")

            # 6. Não permite fechar novamente uma comanda já fechada -> 400
            res_refechar = await client.post(
                f"/api/v1/comandas/{comanda_id}/fechar",
                headers=headers_garcom,
                json={"metodo_pagamento": "dinheiro"},
            )
            assert res_refechar.status_code == 400

            # 7. Mesa 07 foi liberada e pode receber nova comanda aberta
            res_nova_mesa = await client.post(
                "/api/v1/comandas",
                headers=headers_garcom,
                json={"numero_mesa": 7, "identificador": "Mesa 07 - Segundo Giro"},
            )
            assert res_nova_mesa.status_code == 201

            # 8. Venda fechada reflete imediatamente no resumo financeiro do Dono
            res_resumo = await client.get("/api/v1/financeiro/resumo", headers=headers_dono)
            assert res_resumo.status_code == 200
            assert Decimal(res_resumo.json()["total_vendas"]) == Decimal("130.00")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_fechamento_validacoes_schema_rbac_e_idor(db_session: AsyncSession):
    dono_a, rest_a, prato, _, dono_b, _ = await _criar_cenario_fechamento(db_session)

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

            comanda = (
                await client.post(
                    "/api/v1/comandas",
                    headers=headers_a,
                    json={"identificador": "Balcão - Maria", "tipo_atendimento": "balcao"},
                )
            ).json()
            comanda_id = comanda["id"]

            await client.post(
                f"/api/v1/comandas/{comanda_id}/itens",
                headers=headers_a,
                json={"item_id": str(prato.id), "quantidade": 1},
            )

            # 1. Validações de schema: método de pagamento inválido, desconto negativo e extra="forbid"
            assert (
                await client.post(
                    f"/api/v1/comandas/{comanda_id}/fechar",
                    headers=headers_a,
                    json={"metodo_pagamento": "fiado"},
                )
            ).status_code == 422
            assert (
                await client.post(
                    f"/api/v1/comandas/{comanda_id}/fechar",
                    headers=headers_a,
                    json={"metodo_pagamento": "pix", "desconto": "-1.00"},
                )
            ).status_code == 422
            assert (
                await client.post(
                    f"/api/v1/comandas/{comanda_id}/fechar",
                    headers=headers_a,
                    json={"metodo_pagamento": "pix", "valor_total": "0.01"},
                )
            ).status_code == 422

            # 2. BFLA: Cozinha não pode consultar prévia financeira nem fechar comanda -> 403
            assert (
                await client.get(f"/api/v1/comandas/{comanda_id}/previa", headers=headers_cozinha)
            ).status_code == 403
            assert (
                await client.post(
                    f"/api/v1/comandas/{comanda_id}/fechar",
                    headers=headers_cozinha,
                    json={"metodo_pagamento": "pix"},
                )
            ).status_code == 403

            # 3. IDOR: Dono B não pode consultar prévia nem fechar comanda do Restaurante A -> 404
            assert (
                await client.get(f"/api/v1/comandas/{comanda_id}/previa", headers=headers_b)
            ).status_code == 404
            assert (
                await client.post(
                    f"/api/v1/comandas/{comanda_id}/fechar",
                    headers=headers_b,
                    json={"metodo_pagamento": "pix"},
                )
            ).status_code == 404
    finally:
        app.dependency_overrides.clear()
