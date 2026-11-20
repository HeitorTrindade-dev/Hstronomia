from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from typing import Any, Optional

import bcrypt
import jwt

from src.core.config import settings


def hash_password(password: str) -> str:
    """Gera hash seguro da senha com salt automático usando bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


DUMMY_PASSWORD_HASH: str = hash_password("hstronomia-dummy-timing-guard")


def compute_pin_fingerprint(restaurante_id: Any, role: str, pin: str) -> str:
    """Gera fingerprint HMAC-SHA256 truncado do PIN atual para revogação automática de sessão."""
    msg = f"{restaurante_id}:{role}:{pin.strip()}".encode("utf-8")
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        msg,
        hashlib.sha256,
    ).hexdigest()[:16]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto puro coincide com o hash gravado."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Gera token JWT assinado com claims e tempo de expiração."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decodifica e valida assinatura e expiração do token JWT."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
