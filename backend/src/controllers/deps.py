import uuid
from dataclasses import dataclass
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Query, status
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
        restaurante_id_str = payload.get("restaurante_id")
        if not restaurante_id_str:
            raise unauthorized_exception
        try:
            restaurante_uuid = uuid.UUID(restaurante_id_str)
        except ValueError:
            raise unauthorized_exception
        if restaurante_uuid != sub_uuid:
            raise unauthorized_exception

        restaurante_repo = RestauranteRepository(session)
        restaurante = await restaurante_repo.get_by_id(restaurante_uuid)
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


async def get_current_garcom(
    current_user: Annotated[UserSession, Depends(get_current_user)],
) -> UserSession:
    if current_user.role != "garcom" or not current_user.restaurante_id or not current_user.restaurante:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao Garçom.",
        )
    return current_user


async def get_current_cozinha(
    current_user: Annotated[UserSession, Depends(get_current_user)],
) -> UserSession:
    if current_user.role != "cozinha" or not current_user.restaurante_id or not current_user.restaurante:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito à Cozinha.",
        )
    return current_user


async def get_current_operacional(
    current_user: Annotated[UserSession, Depends(get_current_user)],
) -> UserSession:
    if current_user.role not in ("garcom", "cozinha", "dono"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso não autorizado para esta operação.",
        )
    return current_user


async def get_current_atendimento(
    current_user: Annotated[UserSession, Depends(get_current_user)],
) -> UserSession:
    if current_user.role not in ("garcom", "dono"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao Garçom ou Dono.",
        )
    return current_user


async def _resolver_restaurante_do_dono(
    dono: Dono,
    session: AsyncSession,
    restaurante_id: uuid.UUID | None,
) -> uuid.UUID:
    restaurante_repo = RestauranteRepository(session)
    restaurantes = await restaurante_repo.get_by_dono_id(dono.id)

    if restaurante_id is not None:
        if not any(r.id == restaurante_id for r in restaurantes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado a este restaurante.",
            )
        return restaurante_id

    if len(restaurantes) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum restaurante cadastrado para este dono.",
        )
    if len(restaurantes) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe o restaurante_id pois há múltiplos restaurantes cadastrados.",
        )
    return restaurantes[0].id


async def get_dono_restaurante_id(
    current_dono: Annotated[Dono, Depends(get_current_dono)],
    session: Annotated[AsyncSession, Depends(get_db)],
    restaurante_id: Annotated[uuid.UUID | None, Query()] = None,
) -> uuid.UUID:
    """Resolve e valida o restaurante_id pertencente ao Dono autenticado (proteção IDOR)."""
    return await _resolver_restaurante_do_dono(current_dono, session, restaurante_id)


async def _resolver_restaurante_da_sessao(
    current_user: UserSession,
    session: AsyncSession,
    restaurante_id: uuid.UUID | None,
) -> uuid.UUID:
    if current_user.role == "dono" and current_user.dono:
        return await _resolver_restaurante_do_dono(current_user.dono, session, restaurante_id)

    if not current_user.restaurante_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sessão operacional sem restaurante vinculado.",
        )
    if restaurante_id is not None and restaurante_id != current_user.restaurante_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado a este restaurante.",
        )
    return current_user.restaurante_id


async def get_sessao_restaurante_id(
    current_user: Annotated[UserSession, Depends(get_current_operacional)],
    session: Annotated[AsyncSession, Depends(get_db)],
    restaurante_id: Annotated[uuid.UUID | None, Query()] = None,
) -> uuid.UUID:
    """Resolve e valida o restaurante_id da sessão atual (Dono, Garçom ou Cozinha)."""
    return await _resolver_restaurante_da_sessao(current_user, session, restaurante_id)


async def get_atendimento_restaurante_id(
    current_user: Annotated[UserSession, Depends(get_current_atendimento)],
    session: Annotated[AsyncSession, Depends(get_db)],
    restaurante_id: Annotated[uuid.UUID | None, Query()] = None,
) -> uuid.UUID:
    """Resolve e valida o restaurante_id da sessão de atendimento (Garçom ou Dono)."""
    return await _resolver_restaurante_da_sessao(current_user, session, restaurante_id)

