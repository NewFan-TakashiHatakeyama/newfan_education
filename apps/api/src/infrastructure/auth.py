from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from infrastructure.settings import load_settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
settings = load_settings()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(
    *,
    user_id: str,
    role: str,
    tenant_id: str,
    display_name: str,
    expires_delta_minutes: int | None = None,
) -> str:
    expire_minutes = expires_delta_minutes or settings.access_token_expire_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "tenant_id": tenant_id,
        "display_name": display_name,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid access token") from exc
