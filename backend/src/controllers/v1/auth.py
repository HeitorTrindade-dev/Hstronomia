import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.deps import UserSession, get_current_user
from src.core.database import get_db
from src.core.rate_limit import dono_login_rate_limiter, operational_login_rate_limiter
from src.schemas.auth import (
    AuthMeResponse,
    DonoCreate,
    DonoResponse,
    LoginRequest,
    OperacionalLoginRequest,
    TokenResponse,
)
from src.services.auth import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/cadastrar",
    response_model=DonoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo Dono",
)
async def cadastrar_dono(
    data: DonoCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = AuthService(session)
    dono = await service.cadastrar_dono(data)
    await session.commit()
    return dono


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login do Dono",
)
async def login_dono(
    request: Request,
    data: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{data.email}"

    bloqueado, retry_after = dono_login_rate_limiter.is_blocked(rate_key)
    if bloqueado:
        logger.warning(
            "Bloqueio por rate limit no login do Dono (ip=%s, email=%s, retry_after=%ss)",
            client_ip,
            data.email,
            retry_after,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de autenticação. Tente novamente mais tarde.",
            headers={"Retry-After": str(retry_after)},
        )

    service = AuthService(session)
    try:
        response = await service.autenticar_dono(data)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            tentativas = dono_login_rate_limiter.record_failure(rate_key)
            logger.warning(
                "Falha no login do Dono (ip=%s, email=%s, tentativas=%d)",
                client_ip,
                data.email,
                tentativas,
            )
        raise

    dono_login_rate_limiter.reset_key(rate_key)
    return response


@router.post(
    "/operacional",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login operacional por PIN (Garçom ou Cozinha)",
)
async def login_operacional(
    request: Request,
    data: OperacionalLoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{data.slug}"

    bloqueado, retry_after = operational_login_rate_limiter.is_blocked(rate_key)
    if bloqueado:
        logger.warning(
            "Bloqueio por rate limit no login operacional (ip=%s, slug=%s, retry_after=%ss)",
            client_ip,
            data.slug,
            retry_after,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de autenticação. Tente novamente mais tarde.",
            headers={"Retry-After": str(retry_after)},
        )

    service = AuthService(session)
    try:
        response = await service.autenticar_operacional(data)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            tentativas = operational_login_rate_limiter.record_failure(rate_key)
            logger.warning(
                "Falha no login operacional (ip=%s, slug=%s, tentativas=%d)",
                client_ip,
                data.slug,
                tentativas,
            )
        raise

    operational_login_rate_limiter.reset_key(rate_key)
    return response


@router.get(
    "/me",
    response_model=AuthMeResponse,
    status_code=status.HTTP_200_OK,
    summary="Dados da sessão atual (Dono, Garçom ou Cozinha)",
)
async def obter_me(
    current_user: Annotated[UserSession, Depends(get_current_user)],
):
    if current_user.role == "dono" and current_user.dono:
        return AuthMeResponse(
            role="dono",
            dono=DonoResponse.model_validate(current_user.dono),
        )

    return AuthMeResponse(
        role=current_user.role,
        restaurante_id=current_user.restaurante_id,
        restaurante_nome=current_user.restaurante.nome if current_user.restaurante else None,
        restaurante_slug=current_user.restaurante.slug if current_user.restaurante else None,
    )

