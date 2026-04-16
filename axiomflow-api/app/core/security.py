from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def new_token_raw(nbytes: int = 32) -> str:
    return _b64url(secrets.token_bytes(nbytes))


def new_code_raw(length: int = 6) -> str:
    """
    Generate a short human-enterable code.
    Used for password reset "verification code".
    """
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def token_sha256(token_raw: str) -> str:
    # Store hash only (not raw) in DB
    return hashlib.sha256(token_raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class JwtPair:
    access_token: str
    access_expires_at: datetime


def create_access_token(*, subject: str, extra: Optional[Dict[str, Any]] = None) -> JwtPair:
    settings = get_settings()
    exp = now_utc() + timedelta(seconds=settings.JWT_ACCESS_TTL_SECONDS)
    payload: Dict[str, Any] = {
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "sub": subject,
        "exp": int(exp.timestamp()),
        "iat": int(now_utc().timestamp()),
        "typ": "access",
    }
    if extra:
        payload.update(extra)

    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return JwtPair(access_token=token, access_expires_at=exp)


def decode_access_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
            options={"require_sub": True},
        )
    except JWTError as e:
        raise ValueError("invalid_token") from e
    if payload.get("typ") != "access":
        raise ValueError("invalid_token_type")
    return payload


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))

