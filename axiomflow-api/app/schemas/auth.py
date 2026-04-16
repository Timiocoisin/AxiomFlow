from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


_HAS_LETTER_RE = re.compile(r"[A-Za-z]")
_HAS_DIGIT_RE = re.compile(r"\d")


def _validate_password_rule(v: str) -> str:
    if not _HAS_LETTER_RE.search(v) or not _HAS_DIGIT_RE.search(v):
        raise ValueError("password_must_contain_letter_and_digit")
    return v


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_rule(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    access_expires_at: datetime
    token_type: str = "Bearer"


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=10, max_length=512)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    # 6-char human-enterable code (A-Z a-z 0-9)
    token: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("token")
    @classmethod
    def validate_reset_token(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) != 6:
            raise ValueError("reset_code_must_be_6_chars")
        if not re.fullmatch(r"[A-Za-z0-9]{6}", v):
            raise ValueError("reset_code_must_be_alnum")
        return v

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password_rule(v)


class OkResponse(BaseModel):
    ok: bool = True
    message: Optional[str] = None

