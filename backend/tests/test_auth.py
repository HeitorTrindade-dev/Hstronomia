import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import hash_password, verify_password, create_access_token, decode_access_token
from src.main import app


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

        # 5. Rota protegida /api/v1/auth/me com token
        headers = {"Authorization": f"Bearer {token}"}
        res_me = await client.get("/api/v1/auth/me", headers=headers)
        assert res_me.status_code == 200
        assert res_me.json()["email"] == "roberto@restaurante.com"

        # 6. Rota protegida sem token deve falhar
        res_me_unauth = await client.get("/api/v1/auth/me")
        assert res_me_unauth.status_code in (401, 403)

    app.dependency_overrides.clear()
