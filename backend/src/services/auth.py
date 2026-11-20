import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import create_access_token, hash_password, verify_password
from src.models.dono import Dono
from src.repositories.dono import DonoRepository
from src.repositories.restaurante import RestauranteRepository
from src.schemas.auth import (
    DonoCreate,
    DonoResponse,
    LoginRequest,
    OperacionalLoginRequest,
    TokenResponse,
)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.dono_repo = DonoRepository(session)

    async def cadastrar_dono(self, data: DonoCreate) -> Dono:
        existente = await self.dono_repo.get_by_email(data.email)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-mail já cadastrado no sistema.",
            )

        senha_hasheada = hash_password(data.senha)
        dono = await self.dono_repo.create(
            nome=data.nome,
            email=data.email,
            senha_hash=senha_hasheada,
        )
        return dono

    async def autenticar_dono(self, data: LoginRequest) -> TokenResponse:
        # Prevenção OWASP A07: Resposta genérica para evitar enumeração de usuários
        credenciais_invalidas = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

        dono = await self.dono_repo.get_by_email(data.email)
        if not dono:
            raise credenciais_invalidas

        if not verify_password(data.senha, dono.senha_hash):
            raise credenciais_invalidas

        token_data = {
            "sub": str(dono.id),
            "email": dono.email,
            "role": "dono",
        }
        access_token = create_access_token(data=token_data)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            role="dono",
            dono=DonoResponse.model_validate(dono),
        )

    async def autenticar_operacional(self, data: OperacionalLoginRequest) -> TokenResponse:
        credenciais_invalidas = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

        restaurante_repo = RestauranteRepository(self.session)
        restaurante = await restaurante_repo.get_by_slug(data.slug)
        if not restaurante:
            raise credenciais_invalidas

        pin_limpo = data.pin.strip()
        role = None
        if pin_limpo == restaurante.codigo_garcom:
            role = "garcom"
        elif pin_limpo == restaurante.codigo_cozinha:
            role = "cozinha"
        else:
            raise credenciais_invalidas

        token_data = {
            "sub": str(restaurante.id),
            "restaurante_id": str(restaurante.id),
            "role": role,
        }
        access_token = create_access_token(data=token_data)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            role=role,
            restaurante_id=restaurante.id,
            restaurante_nome=restaurante.nome,
            restaurante_slug=restaurante.slug,
        )

    async def obter_dono_por_id(self, dono_id: uuid.UUID) -> Dono:
        dono = await self.dono_repo.get_by_id(dono_id)
        if not dono:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dono não encontrado.",
            )
        return dono
