from decimal import Decimal
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import create_operational_token, hash_password
from src.main import app
from src.repositories.comanda import ComandaRepository
from src.repositories.dono import DonoRepository
from src.repositories.item import ItemRepository
from src.repositories.restaurante import RestauranteRepository


async def _criar_cenario_integridade(db_session: AsyncSession):
    dono_repo = DonoRepository(db_session)
    rest_repo = RestauranteRepository(db_session)
    item_repo = ItemRepository(db_session)

    dono = await dono_repo.create(
        nome="Dono Integridade",
        email="integridade@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    rest = await rest_repo.create(
        dono_id=dono.id,
        nome="Restaurante Integridade",
        slug="rest-integridade",
        codigo_garcom="111111",
        codigo_cozinha="222222",
    )
    item = await item_repo.create(
        restaurante_id=rest.id,
        nome="Picanha na Chapa",
        descricao="400g",
        preco=Decimal("95.00"),
    )
    await db_session.commit()
    return dono, rest, item


@pytest.mark.asyncio
async def test_indice_unico_parcial_mesa_aberta_e_validacao_cruzada_tipo_atendimento(
    db_session: AsyncSession,
):
    _, rest, _ = await _criar_cenario_integridade(db_session)
    rest_id = rest.id
    token_garcom = create_operational_token(rest_id, "garcom", rest.codigo_garcom)
    headers_garcom = {"Authorization": f"Bearer {token_garcom}"}

    # 1. Índice único parcial no banco: bloqueia 2 abertas na mesma mesa, mas permite após fechar/cancelar
    comanda_repo = ComandaRepository(db_session)
    c1 = await comanda_repo.create(restaurante_id=rest_id, numero_mesa=8, tipo_atendimento="mesa")
    c1_id = c1.id
    await db_session.commit()

    with pytest.raises(IntegrityError):
        await comanda_repo.create(restaurante_id=rest_id, numero_mesa=8, tipo_atendimento="mesa")
    await db_session.rollback()

    # Após cancelar c1, outra comanda aberta na mesa 8 é permitida pelo índice parcial
    from datetime import UTC, datetime

    await comanda_repo.cancelar(
        comanda_id=c1_id,
        restaurante_id=rest_id,
        fechado_em=datetime.now(UTC),
    )
    c2 = await comanda_repo.create(restaurante_id=rest_id, numero_mesa=8, tipo_atendimento="mesa")
    await db_session.commit()
    assert c2.status == "aberta"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 2. Simula race condition (TOCTOU): get_aberta_por_mesa retorna None, mas INSERT bate na constraint
            with patch.object(ComandaRepository, "get_aberta_por_mesa", return_value=None):
                res_race = await client.post(
                    "/api/v1/comandas",
                    headers=headers_garcom,
                    json={"numero_mesa": 8, "tipo_atendimento": "mesa"},
                )
                assert res_race.status_code == 409
                assert res_race.json()["detail"] == "Já existe uma comanda aberta para esta mesa."

            # 3. Validação cruzada entre tipo_atendimento e numero_mesa
            # tipo_atendimento="mesa" sem numero_mesa (apenas identificador) -> 422
            assert (
                await client.post(
                    "/api/v1/comandas",
                    headers=headers_garcom,
                    json={"identificador": "Mesa sem número", "tipo_atendimento": "mesa"},
                )
            ).status_code == 422

            # tipo_atendimento="balcao" ou "viagem" informando numero_mesa -> 422
            assert (
                await client.post(
                    "/api/v1/comandas",
                    headers=headers_garcom,
                    json={
                        "numero_mesa": 99,
                        "identificador": "Balcão com mesa",
                        "tipo_atendimento": "balcao",
                    },
                )
            ).status_code == 422
            assert (
                await client.post(
                    "/api/v1/comandas",
                    headers=headers_garcom,
                    json={
                        "numero_mesa": 99,
                        "identificador": "Viagem com mesa",
                        "tipo_atendimento": "viagem",
                    },
                )
            ).status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_kds_filtro_pronto_e_entrega_pelo_garcom(db_session: AsyncSession):
    _, rest, item = await _criar_cenario_integridade(db_session)
    token_garcom = create_operational_token(rest.id, "garcom", rest.codigo_garcom)
    token_cozinha = create_operational_token(rest.id, "cozinha", rest.codigo_cozinha)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers_garcom = {"Authorization": f"Bearer {token_garcom}"}
            headers_cozinha = {"Authorization": f"Bearer {token_cozinha}"}

            comanda = (
                await client.post(
                    "/api/v1/comandas",
                    headers=headers_garcom,
                    json={"numero_mesa": 14, "identificador": "Mesa 14"},
                )
            ).json()
            pedido = (
                await client.post(
                    f"/api/v1/comandas/{comanda['id']}/itens",
                    headers=headers_garcom,
                    json={"item_id": str(item.id), "quantidade": 1},
                )
            ).json()
            url_status = f"/api/v1/cozinha/pedidos/{pedido['id']}/status"

            # 1. Garçom NÃO pode iniciar preparo nem marcar como pronto -> 403
            assert (
                await client.patch(
                    url_status,
                    headers=headers_garcom,
                    json={"status": "em_preparo"},
                )
            ).status_code == 403
            assert (
                await client.patch(
                    url_status,
                    headers=headers_garcom,
                    json={"status": "pronto"},
                )
            ).status_code == 403

            # 2. Cozinha avança para em_preparo e pronto
            assert (
                await client.patch(
                    url_status,
                    headers=headers_cozinha,
                    json={"status": "em_preparo"},
                )
            ).status_code == 200
            assert (
                await client.patch(
                    url_status,
                    headers=headers_cozinha,
                    json={"status": "pronto"},
                )
            ).status_code == 200

            # 3. KDS lista pedidos com ?status=pronto
            res_prontos = await client.get(
                "/api/v1/cozinha/pedidos?status=pronto",
                headers=headers_cozinha,
            )
            assert res_prontos.status_code == 200
            assert [p["id"] for p in res_prontos.json()] == [pedido["id"]]

            # 4. Garçom PODE realizar a transição final 'pronto' -> 'entregue' -> 200
            res_entrega = await client.patch(
                url_status,
                headers=headers_garcom,
                json={"status": "entregue"},
            )
            assert res_entrega.status_code == 200
            assert res_entrega.json()["status"] == "entregue"
    finally:
        app.dependency_overrides.clear()
