import uuid
from dataclasses import dataclass
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import decode_access_token
from src.models.dono import Dono
from src.models.restaurante import Restaurante
from src.repositories.dono import DonoRepository
from src.repositories.restaurante import RestauranteRepository

security_scheme = HTTPBearer(auto_error=True)


@dataclass
class UserSession:
    role: str
    dono: Optional[Dono] = None
    restaurante: Optional[Restaurante] = None
    restaurante_id: Optional[uuid.UUID] = None


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserSession:
    token = credentials.credentials
    payload = decode_access_token(token)

    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not payload:
        raise unauthorized_exception

    sub_str = payload.get("sub")
    role = payload.get("role")

    if not sub_str or not role:
        raise unauthorized_exception

    try:
        sub_uuid = uuid.UUID(sub_str)
    except ValueError:
        raise unauthorized_exception

    if role == "dono":
        dono_repo = DonoRepository(session)
        dono = await dono_repo.get_by_id(sub_uuid)
        if not dono:
            raise unauthorized_exception
        return UserSession(role="dono", dono=dono)

    if role in ("garcom", "cozinha"):
        restaurante_repo = RestauranteRepository(session)
        restaurante = await restaurante_repo.get_by_id(sub_uuid)
        if not restaurante:
            raise unauthorized_exception
        return UserSession(
            role=role,
            restaurante=restaurante,
            restaurante_id=restaurante.id,
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Função de usuário não reconhecida.",
    )


async def get_current_dono(
    current_user: Annotated[UserSession, Depends(get_current_user)],
) -> Dono:
    if current_user.role != "dono" or not current_user.dono:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao Dono do estabelecimento.",
        )
    return current_user.dono


async def get_current_operacional(
    current_user: Annotated[UserSession, Depends(get_current_user)],
) -> UserSession:
    if current_user.role not in ("garcom", "cozinha", "dono"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso não autorizado para esta operação.",
        )
    return current_user

