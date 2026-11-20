import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import create_access_token, hash_password
from src.main import app
from src.repositories.dono import DonoRepository


async def _criar_dois_donos(db_session: AsyncSession):
    dono_repo = DonoRepository(db_session)
    dono_a = await dono_repo.create(
        nome="Dono Restaurante A",
        email="rest_dono_a@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    dono_b = await dono_repo.create(
        nome="Dono Restaurante B",
        email="rest_dono_b@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    await db_session.commit()
    return dono_a, dono_b


@pytest.mark.asyncio
async def test_onboarding_restaurante_listagem_consulta_publica_e_rotacao_pins(
    db_session: AsyncSession,
):
    dono_a, dono_b = await _criar_dois_donos(db_session)
    token_a = create_access_token(
        {"sub": str(dono_a.id), "email": dono_a.email, "role": "dono"}
    )
    token_b = create_access_token(
        {"sub": str(dono_b.id), "email": dono_b.email, "role": "dono"}
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers_a = {"Authorization": f"Bearer {token_a}"}
            headers_b = {"Authorization": f"Bearer {token_b}"}

            # 1. Criação de restaurante pelo Dono A (com normalização de slug)
            res_create = await client.post(
                "/api/v1/restaurantes",
                headers=headers_a,
                json={
                    "nome": "  Cantina Bella Napoli  ",
                    "slug": "  Cantina-Bella-Napoli  ",
                    "codigo_garcom": "123456",
                    "codigo_cozinha": "654321",
                },
            )
            assert res_create.status_code == 201
            rest_a = res_create.json()
            assert rest_a["nome"] == "Cantina Bella Napoli"
            assert rest_a["slug"] == "cantina-bella-napoli"
            assert rest_a["dono_id"] == str(dono_a.id)
            assert rest_a["codigo_garcom"] == "123456"
            assert rest_a["codigo_cozinha"] == "654321"

            # 2. Slug duplicado (mesmo por outro dono) -> 409 Conflict
            res_dup = await client.post(
                "/api/v1/restaurantes",
                headers=headers_b,
                json={
                    "nome": "Outra Cantina",
                    "slug": "cantina-bella-napoli",
                    "codigo_garcom": "111111",
                    "codigo_cozinha": "222222",
                },
            )
            assert res_dup.status_code == 409

            # 3. Listagem de restaurantes isolada por dono_id
            res_list_a = await client.get("/api/v1/restaurantes", headers=headers_a)
            res_list_b = await client.get("/api/v1/restaurantes", headers=headers_b)
            assert res_list_a.status_code == 200
            assert [r["id"] for r in res_list_a.json()] == [rest_a["id"]]
            assert res_list_b.status_code == 200
            assert res_list_b.json() == []

            # 4. Consulta pública por slug (não expõe codigo_garcom, codigo_cozinha nem dono_id)
            res_pub = await client.get("/api/v1/restaurantes/slug/CANTINA-BELLA-NAPOLI")
            assert res_pub.status_code == 200
            pub_data = res_pub.json()
            assert pub_data == {
                "id": rest_a["id"],
                "nome": "Cantina Bella Napoli",
                "slug": "cantina-bella-napoli",
            }
            assert "codigo_garcom" not in pub_data
            assert "codigo_cozinha" not in pub_data
            assert "dono_id" not in pub_data

            assert (
                await client.get("/api/v1/restaurantes/slug/slug-inexistente")
            ).status_code == 404

            # 5. Rotação de PINs e validação de não colisão entre codigo_garcom e codigo_cozinha
            res_colisao = await client.patch(
                f"/api/v1/restaurantes/{rest_a['id']}/pins",
                headers=headers_a,
                json={"codigo_garcom": "654321"},
            )
            assert res_colisao.status_code == 400

            res_pins = await client.patch(
                f"/api/v1/restaurantes/{rest_a['id']}/pins",
                headers=headers_a,
                json={"codigo_garcom": "998877"},
            )
            assert res_pins.status_code == 200
            assert res_pins.json()["codigo_garcom"] == "998877"
            assert res_pins.json()["codigo_cozinha"] == "654321"

            # Login operacional funciona imediatamente com o novo PIN
            res_login_op = await client.post(
                "/api/v1/auth/operacional",
                json={"slug": "cantina-bella-napoli", "pin": "998877"},
            )
            assert res_login_op.status_code == 200
            assert res_login_op.json()["role"] == "garcom"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_restaurante_validacoes_schema_rbac_e_idor(db_session: AsyncSession):
    dono_a, dono_b = await _criar_dois_donos(db_session)
    token_a = create_access_token(
        {"sub": str(dono_a.id), "email": dono_a.email, "role": "dono"}
    )
    token_b = create_access_token(
        {"sub": str(dono_b.id), "email": dono_b.email, "role": "dono"}
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers_a = {"Authorization": f"Bearer {token_a}"}
            headers_b = {"Authorization": f"Bearer {token_b}"}

            rest_a = (
                await client.post(
                    "/api/v1/restaurantes",
                    headers=headers_a,
                    json={
                        "nome": "Burger Lab",
                        "slug": "burger-lab",
                        "codigo_garcom": "1234",
                        "codigo_cozinha": "5678",
                    },
                )
            ).json()

            token_garcom = create_access_token(
                {
                    "sub": rest_a["id"],
                    "restaurante_id": rest_a["id"],
                    "role": "garcom",
                }
            )
            headers_garcom = {"Authorization": f"Bearer {token_garcom}"}

            # 1. Validações de schema: PINs iguais, PIN não numérico, slug inválido, extra="forbid"
            assert (
                await client.post(
                    "/api/v1/restaurantes",
                    headers=headers_a,
                    json={
                        "nome": "Rest Inválido",
                        "slug": "rest-invalido",
                        "codigo_garcom": "1234",
                        "codigo_cozinha": "1234",
                    },
                )
            ).status_code == 422
            assert (
                await client.post(
                    "/api/v1/restaurantes",
                    headers=headers_a,
                    json={
                        "nome": "Rest Inválido",
                        "slug": "slug com espaco!",
                        "codigo_garcom": "1234",
                        "codigo_cozinha": "5678",
                    },
                )
            ).status_code == 422
            assert (
                await client.post(
                    "/api/v1/restaurantes",
                    headers=headers_a,
                    json={
                        "nome": "Rest Inválido",
                        "slug": "rest-ok",
                        "codigo_garcom": "abcd",
                        "codigo_cozinha": "5678",
                    },
                )
            ).status_code == 422
            assert (
                await client.post(
                    "/api/v1/restaurantes",
                    headers=headers_a,
                    json={
                        "nome": "Rest Inválido",
                        "slug": "rest-ok",
                        "codigo_garcom": "1234",
                        "codigo_cozinha": "5678",
                        "dono_id": str(dono_b.id),
                    },
                )
            ).status_code == 422
            assert (
                await client.patch(
                    f"/api/v1/restaurantes/{rest_a['id']}/pins",
                    headers=headers_a,
                    json={},
                )
            ).status_code == 422

            # 2. BFLA: Garçom não pode criar, listar nem alterar PINs de restaurante -> 403
            assert (
                await client.get("/api/v1/restaurantes", headers=headers_garcom)
            ).status_code == 403
            assert (
                await client.post(
                    "/api/v1/restaurantes",
                    headers=headers_garcom,
                    json={
                        "nome": "Rest Garçom",
                        "slug": "rest-garcom",
                        "codigo_garcom": "1234",
                        "codigo_cozinha": "5678",
                    },
                )
            ).status_code == 403
            assert (
                await client.patch(
                    f"/api/v1/restaurantes/{rest_a['id']}/pins",
                    headers=headers_garcom,
                    json={"codigo_garcom": "0000"},
                )
            ).status_code == 403

            # 3. IDOR: Dono B não pode alterar PINs do restaurante do Dono A -> 404
            assert (
                await client.patch(
                    f"/api/v1/restaurantes/{rest_a['id']}/pins",
                    headers=headers_b,
                    json={"codigo_garcom": "0000"},
                )
            ).status_code == 404
    finally:
        app.dependency_overrides.clear()
