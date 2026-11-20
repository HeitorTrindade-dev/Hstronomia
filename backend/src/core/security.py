import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from src.core.config import settings

MAX_BCRYPT_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    """Gera hash seguro da senha com salt automático usando bcrypt."""
    if "\x00" in password:
        raise ValueError("A senha não pode conter caracteres nulos.")
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_BCRYPT_PASSWORD_BYTES:
        raise ValueError("A senha excede o limite máximo de 72 bytes.")
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


# Hash dummy com custo mínimo (rounds=4) para proteção de timing quando e-mail não existe
DUMMY_PASSWORD_HASH: str = bcrypt.hashpw(
    b"hstronomia-dummy-timing-guard",
    bcrypt.gensalt(rounds=4),
).decode("utf-8")


def compute_pin_fingerprint(restaurante_id: Any, role: str, pin: str) -> str:
    """Gera fingerprint HMAC-SHA256 truncado do PIN atual para revogação automática de sessão."""
    msg = f"{restaurante_id}:{role}:{pin.strip()}".encode()
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        msg,
        hashlib.sha256,
    ).hexdigest()[:16]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto puro coincide com o hash gravado."""
    if "\x00" in plain_password:
        return False
    plain_bytes = plain_password.encode("utf-8")
    if len(plain_bytes) > MAX_BCRYPT_PASSWORD_BYTES:
        return False
    try:
        return bcrypt.checkpw(
            plain_bytes,
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Gera token JWT assinado com claims e tempo de expiração."""
    to_encode = data.copy()
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_operational_token(
    restaurante_id: Any,
    role: str,
    pin: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Gera token JWT operacional (Garçom ou Cozinha) com fingerprint do PIN atual."""
    rest_str = str(restaurante_id)
    delta = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.OPERATIONAL_TOKEN_EXPIRE_MINUTES)
    )
    return create_access_token(
        data={
            "sub": rest_str,
            "restaurante_id": rest_str,
            "role": role,
            "pin_fp": compute_pin_fingerprint(rest_str, role, pin),
        },
        expires_delta=delta,
    )


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decodifica e valida assinatura e expiração do token JWT."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
