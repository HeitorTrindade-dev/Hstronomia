import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, settings
from src.core.database import get_db
from src.core.rate_limit import SlidingWindowRateLimiter
from src.core.security import (
    create_access_token,
    create_operational_token,
    hash_password,
    verify_password,
)
from src.main import app
from src.repositories.base import TenantIsolationError
from src.repositories.comanda import ComandaRepository
from src.repositories.dono import DonoRepository
from src.repositories.item import ItemRepository
from src.repositories.restaurante import RestauranteRepository


async def _criar_cenario_consolidado(db_session: AsyncSession):
    dono_repo = DonoRepository(db_session)
    rest_repo = RestauranteRepository(db_session)
    item_repo = ItemRepository(db_session)

    dono_a = await dono_repo.create(
        nome="Dono Consolidado A",
        email="consolidado_a@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    rest_a = await rest_repo.create(
        dono_id=dono_a.id,
        nome="Restaurante Consolidado A",
        slug="rest-consolidado-a",
        codigo_garcom="111222",
        codigo_cozinha="333444",
    )
    item_1 = await item_repo.create(
        restaurante_id=rest_a.id,
        nome="Costela no Bafo",
        descricao="Acompanha mandioca",
        preco=Decimal("80.00"),
    )
    item_2 = await item_repo.create(
        restaurante_id=rest_a.id,
        nome="Refrigerante Lata",
        descricao="350ml",
        preco=Decimal("8.50"),
    )

    dono_b = await dono_repo.create(
        nome="Dono Consolidado B",
        email="consolidado_b@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    rest_b = await rest_repo.create(
        dono_id=dono_b.id,
        nome="Restaurante Consolidado B",
        slug="rest-consolidado-b",
        codigo_garcom="555666",
        codigo_cozinha="777888",
    )
    await db_session.commit()
    return dono_a, rest_a, item_1, item_2, dono_b, rest_b


def test_settings_bcrypt_rounds_e_app_timezone_validacoes():
    # Em produção, BCRYPT_ROUNDS < 12 deve falhar
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="chave-forte-exclusiva-de-producao-com-mais-de-32-chars",
            BCRYPT_ROUNDS=8,
        )

    # APP_TIMEZONE inválido deve falhar
    with pytest.raises(ValidationError):
        Settings(APP_TIMEZONE="Timezone/Inexistente_XYZ")

    # Configuração válida com America/Sao_Paulo
    cfg = Settings(APP_TIMEZONE="America/Sao_Paulo", BCRYPT_ROUNDS=12)
    assert cfg.APP_TIMEZONE == "America/Sao_Paulo"
    assert cfg.BCRYPT_ROUNDS == 12


def test_bcrypt_limite_72_bytes_e_null_bytes():
    with pytest.raises(ValueError):
        hash_password("a" * 73)
    with pytest.raises(ValueError):
        hash_password("senha\x00invalida")

    hashed = hash_password("senha_valida_123")
    assert verify_password("a" * 80, hashed) is False
    assert verify_password("senha\x00invalida", hashed) is False
    assert verify_password("senha_valida_123", "hash-malformado") is False


def test_rate_limiter_max_keys_eviction():
    limiter = SlidingWindowRateLimiter(max_attempts=3, window_seconds=300, max_keys=3)
    limiter.record_failure("ip:user1")
    limiter.record_failure("ip:user2")
    limiter.record_failure("ip:user3")
    assert len(limiter._attempts) == 3

    # Inserir 4ª chave distinta não deve ultrapassar max_keys=3
    limiter.record_failure("ip:user4")
    assert len(limiter._attempts) == 3
    assert "ip:user1" not in limiter._attempts
    assert "ip:user4" in limiter._attempts


@pytest.mark.asyncio
async def test_restaurante_repository_bloqueia_list_all_e_delete_by_id(
    db_session: AsyncSession,
):
    rest_repo = RestauranteRepository(db_session)
    with pytest.raises(TenantIsolationError):
        await rest_repo.list_all()
    with pytest.raises(TenantIsolationError):
        await rest_repo.delete_by_id(uuid.uuid4())


@pytest.mark.asyncio
async def test_cadastro_dono_race_condition_e_validacoes_null_bytes_schemas(
    db_session: AsyncSession,
):
    dono_a, _, _, _, _, _ = await _criar_cenario_consolidado(db_session)
    token_dono = create_access_token(
        {"sub": str(dono_a.id), "email": dono_a.email, "role": "dono"}
    )
    headers_dono = {"Authorization": f"Bearer {token_dono}"}

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Simula race condition (TOCTOU) no cadastro de Dono: get_by_email retorna None mas INSERT falha
            with patch.object(DonoRepository, "get_by_email", return_value=None):
                res_race = await client.post(
                    "/api/v1/auth/cadastrar",
                    json={
                        "nome": "Clone Concorrente",
                        "email": "consolidado_a@hstronomia.com",
                        "senha": "senha_123456",
                    },
                )
                assert res_race.status_code == 400
                assert res_race.json()["detail"] == "E-mail já cadastrado no sistema."

            # 2. Senha > 72 bytes (ex: 30 emojis = 120 bytes UTF-8, mas <= 72 chars) -> 422
            senha_multibyte = "🍕" * 20
            assert (
                await client.post(
                    "/api/v1/auth/cadastrar",
                    json={
                        "nome": "Dono Emoji",
                        "email": "emoji@hstronomia.com",
                        "senha": senha_multibyte,
                    },
                )
            ).status_code == 422
            assert (
                await client.post(
                    "/api/v1/auth/login",
                    json={"email": "emoji@hstronomia.com", "senha": senha_multibyte},
                )
            ).status_code == 422

            # 3. Null bytes em ItemCreate, ItemUpdate, DespesaCreate, DespesaUpdate -> 422
            assert (
                await client.post(
                    "/api/v1/itens",
                    headers=headers_dono,
                    json={"nome": "Prato\x00Nulo", "preco": "25.00"},
                )
            ).status_code == 422
            assert (
                await client.post(
                    "/api/v1/itens",
                    headers=headers_dono,
                    json={"nome": "Prato Ok", "descricao": "Desc\x00Nula", "preco": "25.00"},
                )
            ).status_code == 422
            assert (
                await client.post(
                    "/api/v1/financeiro/despesas",
                    headers=headers_dono,
                    json={
                        "descricao": "Despesa\x00Nula",
                        "categoria": "outros",
                        "valor": "50.00",
                        "data_pagamento": "2026-11-20",
                    },
                )
            ).status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_edicao_remocao_item_comanda_e_bloqueio_fechamento_vazia(
    db_session: AsyncSession,
):
    dono_a, rest_a, item_1, item_2, dono_b, rest_b = await _criar_cenario_consolidado(db_session)
    headers_garcom_a = {
        "Authorization": f"Bearer {create_operational_token(rest_a.id, 'garcom', rest_a.codigo_garcom)}"
    }
    headers_cozinha_a = {
        "Authorization": f"Bearer {create_operational_token(rest_a.id, 'cozinha', rest_a.codigo_cozinha)}"
    }
    headers_dono_a = {
        "Authorization": f"Bearer {create_access_token({'sub': str(dono_a.id), 'email': dono_a.email, 'role': 'dono'})}"
    }
    headers_dono_b = {
        "Authorization": f"Bearer {create_access_token({'sub': str(dono_b.id), 'email': dono_b.email, 'role': 'dono'})}"
    }
    _ = rest_b

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Abre comanda na Mesa 05
            comanda = (
                await client.post(
                    "/api/v1/comandas",
                    headers=headers_garcom_a,
                    json={"numero_mesa": 5, "identificador": "Mesa 05"},
                )
            ).json()
            comanda_id = comanda["id"]

            # 2. Tentar fechar comanda vazia (sem itens) -> 400 Bad Request
            res_fechar_vazia = await client.post(
                f"/api/v1/comandas/{comanda_id}/fechar",
                headers=headers_garcom_a,
                json={"metodo_pagamento": "pix"},
            )
            assert res_fechar_vazia.status_code == 400
            assert "sem itens" in res_fechar_vazia.json()["detail"].lower()

            # 3. Adiciona 2 itens: Costela (1x 80.00) e Refrigerante (2x 8.50 = 17.00) -> subtotal 97.00
            pedido_1 = (
                await client.post(
                    f"/api/v1/comandas/{comanda_id}/itens",
                    headers=headers_garcom_a,
                    json={"item_id": str(item_1.id), "quantidade": 1, "observacao": "Ao ponto"},
                )
            ).json()
            pedido_2 = (
                await client.post(
                    f"/api/v1/comandas/{comanda_id}/itens",
                    headers=headers_garcom_a,
                    json={"item_id": str(item_2.id), "quantidade": 2},
                )
            ).json()

            # Dono altera preço da Costela no cardápio para 110.00 (pedido_1 deve manter 80.00 congelado)
            await client.put(
                f"/api/v1/itens/{item_1.id}",
                headers=headers_dono_a,
                json={"nome": "Costela Premium", "preco": "110.00"},
            )

            # 4. Garçom altera quantidade do pedido_1 (de 1 para 2) e observação via PATCH
            res_patch = await client.patch(
                f"/api/v1/comandas/{comanda_id}/itens/{pedido_1['id']}",
                headers=headers_garcom_a,
                json={"quantidade": 2, "observacao": "  Bem passada  "},
            )
            assert res_patch.status_code == 200
            body_patch = res_patch.json()
            assert body_patch["quantidade"] == 2
            assert body_patch["observacao"] == "Bem passada"
            # Nome e preço permanecem congelados!
            assert body_patch["nome_item"] == "Costela no Bafo"
            assert Decimal(body_patch["preco_unitario"]) == Decimal("80.00")

            # Verifica recálculo do subtotal da comanda: (2 * 80.00) + (2 * 8.50) = 177.00
            detalhe_1 = (
                await client.get(f"/api/v1/comandas/{comanda_id}", headers=headers_garcom_a)
            ).json()
            assert Decimal(detalhe_1["subtotal"]) == Decimal("177.00")
            assert Decimal(detalhe_1["valor_total"]) == Decimal("177.00")

            # 5. BFLA e IDOR na edição/remoção
            assert (
                await client.patch(
                    f"/api/v1/comandas/{comanda_id}/itens/{pedido_1['id']}",
                    headers=headers_cozinha_a,
                    json={"quantidade": 1},
                )
            ).status_code == 403
            assert (
                await client.delete(
                    f"/api/v1/comandas/{comanda_id}/itens/{pedido_2['id']}",
                    headers=headers_cozinha_a,
                )
            ).status_code == 403
            assert (
                await client.patch(
                    f"/api/v1/comandas/{comanda_id}/itens/{pedido_1['id']}",
                    headers=headers_dono_b,
                    json={"quantidade": 1},
                )
            ).status_code == 404
            assert (
                await client.delete(
                    f"/api/v1/comandas/{comanda_id}/itens/{pedido_2['id']}",
                    headers=headers_dono_b,
                )
            ).status_code == 404

            # 6. Garçom remove pedido_2 (pendente) via DELETE -> 204 e subtotal volta para 160.00
            res_del = await client.delete(
                f"/api/v1/comandas/{comanda_id}/itens/{pedido_2['id']}",
                headers=headers_garcom_a,
            )
            assert res_del.status_code == 204

            detalhe_2 = (
                await client.get(f"/api/v1/comandas/{comanda_id}", headers=headers_garcom_a)
            ).json()
            assert len(detalhe_2["itens"]) == 1
            assert Decimal(detalhe_2["subtotal"]) == Decimal("160.00")
            assert Decimal(detalhe_2["valor_total"]) == Decimal("160.00")

            # 7. Cozinha inicia preparo do pedido_1 (status -> em_preparo)
            await client.patch(
                f"/api/v1/cozinha/pedidos/{pedido_1['id']}/status",
                headers=headers_cozinha_a,
                json={"status": "em_preparo"},
            )

            # Não é permitido editar nem remover item que já entrou em preparo -> 400
            assert (
                await client.patch(
                    f"/api/v1/comandas/{comanda_id}/itens/{pedido_1['id']}",
                    headers=headers_garcom_a,
                    json={"quantidade": 1},
                )
            ).status_code == 400
            assert (
                await client.delete(
                    f"/api/v1/comandas/{comanda_id}/itens/{pedido_1['id']}",
                    headers=headers_garcom_a,
                )
            ).status_code == 400
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_reativar_item_desativado_e_timezone_resumo_financeiro(
    db_session: AsyncSession,
):
    dono_a, rest_a, item_1, _, dono_b, _ = await _criar_cenario_consolidado(db_session)
    headers_dono_a = {
        "Authorization": f"Bearer {create_access_token({'sub': str(dono_a.id), 'email': dono_a.email, 'role': 'dono'})}"
    }
    headers_dono_b = {
        "Authorization": f"Bearer {create_access_token({'sub': str(dono_b.id), 'email': dono_b.email, 'role': 'dono'})}"
    }
    headers_garcom_a = {
        "Authorization": f"Bearer {create_operational_token(rest_a.id, 'garcom', rest_a.codigo_garcom)}"
    }

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Tentar reativar item que já está ativo -> 400
            assert (
                await client.patch(
                    f"/api/v1/itens/{item_1.id}/reativar",
                    headers=headers_dono_a,
                )
            ).status_code == 400

            # 2. Desativa item_1 via DELETE (soft-delete)
            res_soft = await client.delete(f"/api/v1/itens/{item_1.id}", headers=headers_dono_a)
            assert res_soft.status_code == 200
            assert res_soft.json()["ativo"] is False

            # BFLA e IDOR na reativação
            assert (
                await client.patch(
                    f"/api/v1/itens/{item_1.id}/reativar",
                    headers=headers_garcom_a,
                )
            ).status_code == 403
            assert (
                await client.patch(
                    f"/api/v1/itens/{item_1.id}/reativar",
                    headers=headers_dono_b,
                )
            ).status_code == 404

            # 3. Dono A reativa o item com disponivel=True
            res_reativar = await client.patch(
                f"/api/v1/itens/{item_1.id}/reativar",
                headers=headers_dono_a,
                json={"disponivel": True},
            )
            assert res_reativar.status_code == 200
            body_reat = res_reativar.json()
            assert body_reat["ativo"] is True
            assert body_reat["disponivel"] is True

            # 4. Teste de APP_TIMEZONE no resumo financeiro (venda às 22:30 de 2026-11-20 em America/Sao_Paulo = 01:30Z do dia 21)
            comanda_repo = ComandaRepository(db_session)
            c_noite = await comanda_repo.create(restaurante_id=rest_a.id, numero_mesa=33)
            await comanda_repo.fechar(
                comanda_id=c_noite.id,
                restaurante_id=rest_a.id,
                subtotal=Decimal("200.00"),
                taxa_servico=Decimal("0.00"),
                desconto=Decimal("0.00"),
                valor_total=Decimal("200.00"),
                metodo_pagamento="pix",
                fechado_em=datetime(2026, 11, 21, 1, 30, 0, tzinfo=UTC),
            )
            await db_session.commit()

            tz_original = settings.APP_TIMEZONE
            try:
                settings.APP_TIMEZONE = "America/Sao_Paulo"
                res_br = await client.get(
                    "/api/v1/financeiro/resumo?data_inicio=2026-11-20&data_fim=2026-11-20",
                    headers=headers_dono_a,
                )
                assert res_br.status_code == 200
                assert Decimal(res_br.json()["total_vendas"]) == Decimal("200.00")
            finally:
                settings.APP_TIMEZONE = tz_original
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_edicao_restaurante_edicao_comanda_e_validacao_item_update(
    db_session: AsyncSession,
):
    dono_a, rest_a, item_1, _, dono_b, rest_b = await _criar_cenario_consolidado(db_session)
    headers_dono_a = {
        "Authorization": f"Bearer {create_access_token({'sub': str(dono_a.id), 'email': dono_a.email, 'role': 'dono'})}"
    }
    headers_dono_b = {
        "Authorization": f"Bearer {create_access_token({'sub': str(dono_b.id), 'email': dono_b.email, 'role': 'dono'})}"
    }
    headers_garcom_a = {
        "Authorization": f"Bearer {create_operational_token(rest_a.id, 'garcom', rest_a.codigo_garcom)}"
    }
    headers_cozinha_a = {
        "Authorization": f"Bearer {create_operational_token(rest_a.id, 'cozinha', rest_a.codigo_cozinha)}"
    }

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Validação estrita em ItemUpdate: payload vazio {} ou campos obrigatórios nulos -> 422
            for bad_item_update in (
                {},
                {"nome": None},
                {"preco": None},
                {"disponivel": None},
            ):
                assert (
                    await client.put(
                        f"/api/v1/itens/{item_1.id}",
                        headers=headers_dono_a,
                        json=bad_item_update,
                    )
                ).status_code == 422

            # 2. Edição de dados do Restaurante (PATCH /api/v1/restaurantes/{id})
            # Conflito de slug com restaurante B -> 409
            assert (
                await client.patch(
                    f"/api/v1/restaurantes/{rest_a.id}",
                    headers=headers_dono_a,
                    json={"slug": rest_b.slug},
                )
            ).status_code == 409

            # BFLA (Garçom -> 403) e IDOR (Dono B -> 404)
            assert (
                await client.patch(
                    f"/api/v1/restaurantes/{rest_a.id}",
                    headers=headers_garcom_a,
                    json={"nome": "Hack"},
                )
            ).status_code == 403
            assert (
                await client.patch(
                    f"/api/v1/restaurantes/{rest_a.id}",
                    headers=headers_dono_b,
                    json={"nome": "Hack"},
                )
            ).status_code == 404

            # Atualização legítima de nome e slug
            res_rest_patch = await client.patch(
                f"/api/v1/restaurantes/{rest_a.id}",
                headers=headers_dono_a,
                json={"nome": "  Cantina Alpha Renovada  ", "slug": "  Cantina-Alpha-Renovada  "},
            )
            assert res_rest_patch.status_code == 200
            assert res_rest_patch.json()["nome"] == "Cantina Alpha Renovada"
            assert res_rest_patch.json()["slug"] == "cantina-alpha-renovada"

            # 3. Edição / Troca de Mesa de Comanda (PATCH /api/v1/comandas/{id})
            c_mesa_10 = (
                await client.post(
                    "/api/v1/comandas",
                    headers=headers_garcom_a,
                    json={"numero_mesa": 10, "identificador": "Mesa 10"},
                )
            ).json()
            c_mesa_11 = (
                await client.post(
                    "/api/v1/comandas",
                    headers=headers_garcom_a,
                    json={"numero_mesa": 11, "identificador": "Mesa 11"},
                )
            ).json()

            # Conflito ao tentar mover Mesa 10 para a Mesa 11 já ocupada -> 409
            assert (
                await client.patch(
                    f"/api/v1/comandas/{c_mesa_10['id']}",
                    headers=headers_garcom_a,
                    json={"numero_mesa": 11},
                )
            ).status_code == 409

            # BFLA (Cozinha -> 403) e IDOR (Dono B -> 404)
            assert (
                await client.patch(
                    f"/api/v1/comandas/{c_mesa_10['id']}",
                    headers=headers_cozinha_a,
                    json={"numero_mesa": 15},
                )
            ).status_code == 403
            assert (
                await client.patch(
                    f"/api/v1/comandas/{c_mesa_10['id']}",
                    headers=headers_dono_b,
                    json={"numero_mesa": 15},
                )
            ).status_code == 404

            # Troca legítima da Mesa 10 para a Mesa 15 e atualização do identificador
            res_troca = await client.patch(
                f"/api/v1/comandas/{c_mesa_10['id']}",
                headers=headers_garcom_a,
                json={"numero_mesa": 15, "identificador": "  Mesa 15 - Família  "},
            )
            assert res_troca.status_code == 200
            assert res_troca.json()["numero_mesa"] == 15
            assert res_troca.json()["identificador"] == "Mesa 15 - Família"

            # Conversão para viagem exige remover numero_mesa (consistência cruzada)
            assert (
                await client.patch(
                    f"/api/v1/comandas/{c_mesa_11['id']}",
                    headers=headers_garcom_a,
                    json={"tipo_atendimento": "viagem"},
                )
            ).status_code == 400

            res_conv = await client.patch(
                f"/api/v1/comandas/{c_mesa_11['id']}",
                headers=headers_garcom_a,
                json={
                    "tipo_atendimento": "viagem",
                    "numero_mesa": None,
                    "identificador": "Viagem - Cliente Mesa 11",
                },
            )
            assert res_conv.status_code == 200
            assert res_conv.json()["tipo_atendimento"] == "viagem"
            assert res_conv.json()["numero_mesa"] is None
    finally:
        app.dependency_overrides.clear()
