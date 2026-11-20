from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.deps import get_current_dono
from src.core.database import get_db
from src.models.dono import Dono
from src.schemas.auth import DonoCreate, DonoResponse, LoginRequest, TokenResponse
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


@router.get(
    "/me",
    response_model=DonoResponse,
    status_code=status.HTTP_200_OK,
    summary="Dados do Dono logado",
)
async def obter_me(
    current_dono: Annotated[Dono, Depends(get_current_dono)],
):
    return current_dono
