import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import decode_access_token
from src.models.dono import Dono
from src.repositories.dono import DonoRepository

security_scheme = HTTPBearer(auto_error=True)


async def get_current_dono(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Dono:
    token = credentials.credentials
    payload = decode_access_token(token)

    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not payload:
        raise unauthorized_exception

    user_id_str = payload.get("sub")
    role = payload.get("role")

    if not user_id_str or role != "dono":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso não autorizado para esta função.",
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise unauthorized_exception

    dono_repo = DonoRepository(session)
    dono = await dono_repo.get_by_id(user_uuid)
    if not dono:
        raise unauthorized_exception

    return dono
