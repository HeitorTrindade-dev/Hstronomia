import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from src.main import app
from src.repositories.restaurante import RestauranteRepository


def test_password_hashing():
    senha = "minha_senha_secreta"
    hashed = hash_password(senha)
    assert hashed != senha
    assert verify_password(senha, hashed) is True
    assert verify_password("senha_errada", hashed) is False


def test_jwt_token_generation_and_decoding():
    payload = {"sub": "12345", "role": "dono"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "12345"
    assert decoded["role"] == "dono"

    # Token inválido
    assert decode_access_token("token.invalido.aqui") is None


@pytest.mark.asyncio
async def test_auth_endpoints_flow(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Cadastro de Dono
        cadastro_payload = {
            "nome": "Roberto Dono",
            "email": "roberto@restaurante.com",
            "senha": "senha_segura_123",
        }
        res_cad = await client.post("/api/v1/auth/cadastrar", json=cadastro_payload)
        assert res_cad.status_code == 201
        data_cad = res_cad.json()
        assert data_cad["nome"] == "Roberto Dono"
        assert data_cad["email"] == "roberto@restaurante.com"
        assert "senha_hash" not in data_cad

        # 2. Cadastro duplicado deve falhar (400)
        res_dup = await client.post("/api/v1/auth/cadastrar", json=cadastro_payload)
        assert res_dup.status_code == 400

        # 3. Login com senha errada deve falhar (401 com erro genérico)
        res_err = await client.post(
            "/api/v1/auth/login",
            json={"email": "roberto@restaurante.com", "senha": "senha_errada"},
        )
        assert res_err.status_code == 401
        assert res_err.json()["detail"] == "Credenciais inválidas."

        # 4. Login com sucesso
        res_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "roberto@restaurante.com", "senha": "senha_segura_123"},
        )
        assert res_login.status_code == 200
        data_login = res_login.json()
        assert "access_token" in data_login
        assert data_login["role"] == "dono"
        token = data_login["access_token"]

        # 5. Rota protegida /api/v1/auth/me com token de dono
        headers = {"Authorization": f"Bearer {token}"}
        res_me = await client.get("/api/v1/auth/me", headers=headers)
        assert res_me.status_code == 200
        me_data = res_me.json()
        assert me_data["role"] == "dono"
        assert me_data["dono"]["email"] == "roberto@restaurante.com"

        # 6. Rota protegida sem token deve falhar
        res_me_unauth = await client.get("/api/v1/auth/me")
        assert res_me_unauth.status_code in (401, 403)

        # 7. Criar restaurante no banco para testar logins operacionais
        import uuid
        dono_id = uuid.UUID(data_cad["id"])
        restaurante_repo = RestauranteRepository(db_session)
        await restaurante_repo.create(
            dono_id=dono_id,
            nome="Pizzaria Bella",
            slug="pizzaria-bella",
            codigo_garcom="1234",
            codigo_cozinha="5678",
        )
        await db_session.commit()

        # 8. Login operacional com PIN inválido (401 com erro genérico)
        res_op_err = await client.post(
            "/api/v1/auth/operacional",
            json={"slug": "pizzaria-bella", "pin": "9999"},
        )
        assert res_op_err.status_code == 401
        assert res_op_err.json()["detail"] == "Credenciais inválidas."

        # 9. Login operacional Garçom (sucesso)
        res_garcom = await client.post(
            "/api/v1/auth/operacional",
            json={"slug": "pizzaria-bella", "pin": "1234"},
        )
        assert res_garcom.status_code == 200
        data_garcom = res_garcom.json()
        assert data_garcom["role"] == "garcom"
        assert data_garcom["restaurante_slug"] == "pizzaria-bella"
        token_garcom = data_garcom["access_token"]

        # 10. Garçom chamando /api/v1/auth/me
        headers_garcom = {"Authorization": f"Bearer {token_garcom}"}
        res_me_garcom = await client.get("/api/v1/auth/me", headers=headers_garcom)
        assert res_me_garcom.status_code == 200
        me_garcom = res_me_garcom.json()
        assert me_garcom["role"] == "garcom"
        assert me_garcom["dono"] is None
        assert me_garcom["restaurante_slug"] == "pizzaria-bella"

        # 11. Login operacional Cozinha (sucesso)
        res_cozinha = await client.post(
            "/api/v1/auth/operacional",
            json={"slug": "pizzaria-bella", "pin": "5678"},
        )
        assert res_cozinha.status_code == 200
        data_cozinha = res_cozinha.json()
        assert data_cozinha["role"] == "cozinha"
        token_cozinha = data_cozinha["access_token"]

        # 12. Cozinha chamando /api/v1/auth/me
        headers_cozinha = {"Authorization": f"Bearer {token_cozinha}"}
        res_me_cozinha = await client.get("/api/v1/auth/me", headers=headers_cozinha)
        assert res_me_cozinha.status_code == 200
        me_cozinha = res_me_cozinha.json()
        assert me_cozinha["role"] == "cozinha"
        assert me_cozinha["dono"] is None
        assert me_cozinha["restaurante_slug"] == "pizzaria-bella"

    app.dependency_overrides.clear()
