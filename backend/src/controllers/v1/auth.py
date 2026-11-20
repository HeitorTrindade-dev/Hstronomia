from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.deps import UserSession, get_current_user
from src.core.database import get_db
from src.schemas.auth import (
    AuthMeResponse,
    DonoCreate,
    DonoResponse,
    LoginRequest,
    OperacionalLoginRequest,
    TokenResponse,
)
from src.services.auth import AuthService

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
    data: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = AuthService(session)
    return await service.autenticar_dono(data)


@router.post(
    "/operacional",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login operacional por PIN (Garçom ou Cozinha)",
)
async def login_operacional(
    data: OperacionalLoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = AuthService(session)
    return await service.autenticar_operacional(data)


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

