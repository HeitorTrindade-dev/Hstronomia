import uuid
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.deps import (
    UserSession,
    get_current_cozinha,
    get_current_dono,
    get_current_garcom,
)
from src.core.config import settings
from src.core.database import get_db
from src.core.rate_limit import SlidingWindowRateLimiter
from src.core.security import create_access_token, decode_access_token, hash_password
from src.main import app
from src.models.dono import Dono
from src.repositories.dono import DonoRepository
from src.repositories.restaurante import RestauranteRepository


async def _criar_dono_e_restaurante(
    db_session: AsyncSession,
    *,
    email: str = "dono@hstronomia.com",
    slug: str = "bistro-central",
    codigo_garcom: str = "123456",
    codigo_cozinha: str = "654321",
):
    dono_repo = DonoRepository(db_session)
    dono = await dono_repo.create(
        nome="Chef Dono",
        email=email,
        senha_hash=hash_password("senha_segura_123"),
    )
    restaurante_repo = RestauranteRepository(db_session)
    restaurante = await restaurante_repo.create(
        dono_id=dono.id,
        nome="Bistrô Central",
        slug=slug,
        codigo_garcom=codigo_garcom,
        codigo_cozinha=codigo_cozinha,
    )
    await db_session.commit()
    return dono, restaurante


def test_sliding_window_rate_limiter_bloqueio_e_reset():
    limiter = SlidingWindowRateLimiter(max_attempts=3, window_seconds=60)
    key = "127.0.0.1:bistro-central"

    assert limiter.is_blocked(key) == (False, 0)
    assert limiter.record_failure(key) == 1
    assert limiter.record_failure(key) == 2
    assert limiter.is_blocked(key) == (False, 0)

    assert limiter.record_failure(key) == 3
    blocked, retry_after = limiter.is_blocked(key)
    assert blocked is True
    assert 1 <= retry_after <= 60

    limiter.reset_key(key)
    assert limiter.is_blocked(key) == (False, 0)


@pytest.mark.asyncio
async def test_login_operacional_garcom_e_cozinha_claims_e_expiracao(db_session: AsyncSession):
    _, restaurante = await _criar_dono_e_restaurante(db_session)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Garçom com slug em maiúsculas e espaços (normalização)
            res_garcom = await client.post(
                "/api/v1/auth/operacional",
                json={"slug": "  BISTRO-CENTRAL  ", "pin": "123456"},
            )
            assert res_garcom.status_code == 200
            data_garcom = res_garcom.json()
            assert data_garcom["role"] == "garcom"
            assert data_garcom["restaurante_id"] == str(restaurante.id)
            assert data_garcom["restaurante_slug"] == "bistro-central"

            payload_garcom = decode_access_token(data_garcom["access_token"])
            assert payload_garcom is not None
            assert payload_garcom["role"] == "garcom"
            assert payload_garcom["sub"] == str(restaurante.id)
            assert payload_garcom["restaurante_id"] == str(restaurante.id)
            assert payload_garcom["exp"] - payload_garcom["iat"] == settings.OPERATIONAL_TOKEN_EXPIRE_MINUTES * 60

            # Cozinha
            res_cozinha = await client.post(
                "/api/v1/auth/operacional",
                json={"slug": "bistro-central", "pin": "654321"},
            )
            assert res_cozinha.status_code == 200
            data_cozinha = res_cozinha.json()
            assert data_cozinha["role"] == "cozinha"
            assert data_cozinha["restaurante_id"] == str(restaurante.id)

            payload_cozinha = decode_access_token(data_cozinha["access_token"])
            assert payload_cozinha is not None
            assert payload_cozinha["role"] == "cozinha"
            assert payload_cozinha["restaurante_id"] == str(restaurante.id)
            assert payload_cozinha["exp"] - payload_cozinha["iat"] == settings.OPERATIONAL_TOKEN_EXPIRE_MINUTES * 60
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_operacional_validacoes_schema_e_anti_enumeracao(db_session: AsyncSession):
    await _criar_dono_e_restaurante(db_session)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # PIN não numérico -> 422
            res_alpha = await client.post(
                "/api/v1/auth/operacional",
                json={"slug": "bistro-central", "pin": "abcd12"},
            )
            assert res_alpha.status_code == 422

            # Campo extra não permitido (extra="forbid") -> 422
            res_extra = await client.post(
                "/api/v1/auth/operacional",
                json={"slug": "bistro-central", "pin": "123456", "role": "dono"},
            )
            assert res_extra.status_code == 422

            # Slug inexistente e PIN inválido retornam a mesma mensagem genérica (OWASP A07)
            res_slug_err = await client.post(
                "/api/v1/auth/operacional",
                json={"slug": "nao-existe", "pin": "123456"},
            )
            res_pin_err = await client.post(
                "/api/v1/auth/operacional",
                json={"slug": "bistro-central", "pin": "000000"},
            )
            assert res_slug_err.status_code == 401
            assert res_pin_err.status_code == 401
            assert res_slug_err.json()["detail"] == "Credenciais inválidas."
            assert res_pin_err.json()["detail"] == "Credenciais inválidas."
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_operacional_rate_limit_forca_bruta(db_session: AsyncSession):
    await _criar_dono_e_restaurante(db_session, slug="restaurante-a")
    await _criar_dono_e_restaurante(
        db_session,
        email="outro@hstronomia.com",
        slug="restaurante-b",
        codigo_garcom="111111",
        codigo_cozinha="222222",
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Atinge o limite de tentativas falhas para restaurante-a
            for _ in range(settings.OPERATIONAL_RATE_LIMIT_MAX_ATTEMPTS):
                res = await client.post(
                    "/api/v1/auth/operacional",
                    json={"slug": "restaurante-a", "pin": "999999"},
                )
                assert res.status_code == 401

            # Próxima tentativa (mesmo com PIN correto) deve ser bloqueada com 429
            res_blocked = await client.post(
                "/api/v1/auth/operacional",
                json={"slug": "restaurante-a", "pin": "123456"},
            )
            assert res_blocked.status_code == 429
            assert "Retry-After" in res_blocked.headers

            # Outro slug não foi bloqueado
            res_outro = await client.post(
                "/api/v1/auth/operacional",
                json={"slug": "restaurante-b", "pin": "111111"},
            )
            assert res_outro.status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dependencias_autorizacao_garcom_cozinha_dono(db_session: AsyncSession):
    dono, restaurante = await _criar_dono_e_restaurante(db_session)

    test_app = FastAPI()

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db

    @test_app.get("/rota-garcom")
    async def rota_garcom(sessao: Annotated[UserSession, Depends(get_current_garcom)]):
        return {"role": sessao.role, "restaurante_id": str(sessao.restaurante_id)}

    @test_app.get("/rota-cozinha")
    async def rota_cozinha(sessao: Annotated[UserSession, Depends(get_current_cozinha)]):
        return {"role": sessao.role, "restaurante_id": str(sessao.restaurante_id)}

    @test_app.get("/rota-dono")
    async def rota_dono(current_dono: Annotated[Dono, Depends(get_current_dono)]):
        return {"dono_id": str(current_dono.id)}

    token_dono = create_access_token({"sub": str(dono.id), "email": dono.email, "role": "dono"})
    token_garcom = create_access_token(
        {"sub": str(restaurante.id), "restaurante_id": str(restaurante.id), "role": "garcom"}
    )
    token_cozinha = create_access_token(
        {"sub": str(restaurante.id), "restaurante_id": str(restaurante.id), "role": "cozinha"}
    )
    token_garcom_sem_restaurante_id = create_access_token({"sub": str(restaurante.id), "role": "garcom"})
    token_garcom_mismatch = create_access_token(
        {"sub": str(restaurante.id), "restaurante_id": str(uuid.uuid4()), "role": "garcom"}
    )

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        # Garçom acessa apenas /rota-garcom
        res = await client.get("/rota-garcom", headers={"Authorization": f"Bearer {token_garcom}"})
        assert res.status_code == 200
        assert res.json() == {"role": "garcom", "restaurante_id": str(restaurante.id)}

        assert (await client.get("/rota-cozinha", headers={"Authorization": f"Bearer {token_garcom}"})).status_code == 403
        assert (await client.get("/rota-dono", headers={"Authorization": f"Bearer {token_garcom}"})).status_code == 403

        # Cozinha acessa apenas /rota-cozinha
        res = await client.get("/rota-cozinha", headers={"Authorization": f"Bearer {token_cozinha}"})
        assert res.status_code == 200
        assert res.json() == {"role": "cozinha", "restaurante_id": str(restaurante.id)}

        assert (await client.get("/rota-garcom", headers={"Authorization": f"Bearer {token_cozinha}"})).status_code == 403
        assert (await client.get("/rota-dono", headers={"Authorization": f"Bearer {token_cozinha}"})).status_code == 403

        # Dono acessa /rota-dono mas não rotas exclusivas de garçom/cozinha
        assert (await client.get("/rota-dono", headers={"Authorization": f"Bearer {token_dono}"})).status_code == 200
        assert (await client.get("/rota-garcom", headers={"Authorization": f"Bearer {token_dono}"})).status_code == 403
        assert (await client.get("/rota-cozinha", headers={"Authorization": f"Bearer {token_dono}"})).status_code == 403

        # Tokens operacionais malformados (sem restaurante_id ou com divergência) -> 401
        assert (
            await client.get("/rota-garcom", headers={"Authorization": f"Bearer {token_garcom_sem_restaurante_id}"})
        ).status_code == 401
        assert (
            await client.get("/rota-garcom", headers={"Authorization": f"Bearer {token_garcom_mismatch}"})
        ).status_code == 401
