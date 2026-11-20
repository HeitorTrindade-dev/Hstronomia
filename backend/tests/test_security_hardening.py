from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import DEFAULT_DEV_SECRET_KEY, Settings, settings
from src.core.database import get_db
from src.core.security import DUMMY_PASSWORD_HASH
from src.main import app


def test_validacao_settings_producao_secret_key_e_debug():
    # Chave default de desenvolvimento em produção -> erro
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY=DEFAULT_DEV_SECRET_KEY,
        )

    # Chave curta (< 32 chars) em produção -> erro
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="chave-curta-demais",
        )

    # DEBUG=True em produção -> erro
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            DEBUG=True,
            SECRET_KEY="chave-forte-exclusiva-de-producao-com-mais-de-32-chars",
        )

    # Configuração válida de produção -> sucesso
    prod_settings = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        SECRET_KEY="chave-forte-exclusiva-de-producao-com-mais-de-32-chars",
    )
    assert prod_settings.ENVIRONMENT == "production"
    assert prod_settings.DEBUG is False


@pytest.mark.asyncio
async def test_security_headers_e_hardening_schemas_dono(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Verifica presença dos headers HTTP de segurança (OWASP A05)
            res_health = await client.get("/api/v1/health")
            assert res_health.status_code == 200
            assert res_health.headers.get("X-Content-Type-Options") == "nosniff"
            assert res_health.headers.get("X-Frame-Options") == "DENY"
            assert res_health.headers.get("Referrer-Policy") == "no-referrer"

            # 2. extra="forbid" em DonoCreate e LoginRequest -> 422
            assert (
                await client.post(
                    "/api/v1/auth/cadastrar",
                    json={
                        "nome": "Dono Extra",
                        "email": "extra@hstronomia.com",
                        "senha": "senha_segura_123",
                        "role": "admin",
                    },
                )
            ).status_code == 422
            assert (
                await client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "extra@hstronomia.com",
                        "senha": "senha_segura_123",
                        "admin": True,
                    },
                )
            ).status_code == 422

            # 3. Normalização case-insensitive de e-mail no cadastro e login
            res_cad = await client.post(
                "/api/v1/auth/cadastrar",
                json={
                    "nome": "  Maria Silva  ",
                    "email": "Maria.Silva@Hstronomia.COM",
                    "senha": "senha_segura_123",
                },
            )
            assert res_cad.status_code == 201
            assert res_cad.json()["email"] == "maria.silva@hstronomia.com"
            assert res_cad.json()["nome"] == "Maria Silva"

            res_login = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "MARIA.SILVA@hstronomia.com",
                    "senha": "senha_segura_123",
                },
            )
            assert res_login.status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_dono_timing_attack_guard_e_rate_limiting(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post(
                "/api/v1/auth/cadastrar",
                json={
                    "nome": "Dono Rate Limit",
                    "email": "ratelimit@hstronomia.com",
                    "senha": "senha_correta_123",
                },
            )

            # 1. Mitigação de timing attack: quando e-mail não existe, verify_password roda com DUMMY_PASSWORD_HASH
            with patch("src.services.auth.verify_password", return_value=False) as mock_verify:
                res_inexistente = await client.post(
                    "/api/v1/auth/login",
                    json={"email": "naoexiste@hstronomia.com", "senha": "qualquer_senha"},
                )
                assert res_inexistente.status_code == 401
                mock_verify.assert_called_once_with("qualquer_senha", DUMMY_PASSWORD_HASH)

            # 2. Rate limit por ip:email no login do Dono (mesmo variando maiúsculas/minúsculas)
            for i in range(settings.OPERATIONAL_RATE_LIMIT_MAX_ATTEMPTS):
                email_variante = (
                    "RATELIMIT@hstronomia.com" if i % 2 == 0 else "ratelimit@hstronomia.com"
                )
                res_err = await client.post(
                    "/api/v1/auth/login",
                    json={"email": email_variante, "senha": "senha_errada"},
                )
                assert res_err.status_code == 401

            # Próxima tentativa (mesmo com senha correta) deve retornar 429 + Retry-After
            res_blocked = await client.post(
                "/api/v1/auth/login",
                json={"email": "ratelimit@hstronomia.com", "senha": "senha_correta_123"},
            )
            assert res_blocked.status_code == 429
            assert "Retry-After" in res_blocked.headers
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_revogacao_imediata_token_operacional_ao_rotacionar_pin(
    db_session: AsyncSession,
):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post(
                "/api/v1/auth/cadastrar",
                json={
                    "nome": "Dono Rotação PIN",
                    "email": "rotacao@hstronomia.com",
                    "senha": "senha_segura_123",
                },
            )
            token_dono = (
                await client.post(
                    "/api/v1/auth/login",
                    json={"email": "rotacao@hstronomia.com", "senha": "senha_segura_123"},
                )
            ).json()["access_token"]
            headers_dono = {"Authorization": f"Bearer {token_dono}"}

            rest = (
                await client.post(
                    "/api/v1/restaurantes",
                    headers=headers_dono,
                    json={
                        "nome": "Restaurante PIN Seguro",
                        "slug": "rest-pin-seguro",
                        "codigo_garcom": "111222",
                        "codigo_cozinha": "333444",
                    },
                )
            ).json()

            # Garçom e Cozinha autenticam via PIN
            token_garcom_antigo = (
                await client.post(
                    "/api/v1/auth/operacional",
                    json={"slug": "rest-pin-seguro", "pin": "111222"},
                )
            ).json()["access_token"]
            token_cozinha = (
                await client.post(
                    "/api/v1/auth/operacional",
                    json={"slug": "rest-pin-seguro", "pin": "333444"},
                )
            ).json()["access_token"]

            assert (
                await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token_garcom_antigo}"},
                )
            ).status_code == 200
            assert (
                await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token_cozinha}"},
                )
            ).status_code == 200

            # Dono rotaciona apenas o PIN do Garçom
            res_patch = await client.patch(
                f"/api/v1/restaurantes/{rest['id']}/pins",
                headers=headers_dono,
                json={"codigo_garcom": "999888"},
            )
            assert res_patch.status_code == 200

            # Token antigo do Garçom é imediatamente revogado (401)
            assert (
                await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token_garcom_antigo}"},
                )
            ).status_code == 401

            # Token da Cozinha (cujo PIN não mudou) permanece válido (200)
            assert (
                await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token_cozinha}"},
                )
            ).status_code == 200

            # Novo login do Garçom com novo PIN gera token válido
            token_garcom_novo = (
                await client.post(
                    "/api/v1/auth/operacional",
                    json={"slug": "rest-pin-seguro", "pin": "999888"},
                )
            ).json()["access_token"]
            assert (
                await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token_garcom_novo}"},
                )
            ).status_code == 200
    finally:
        app.dependency_overrides.clear()
