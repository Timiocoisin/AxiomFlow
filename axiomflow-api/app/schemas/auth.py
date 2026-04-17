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


class SlideCaptchaProof(BaseModel):
    captcha_id: str = Field(min_length=8, max_length=128)
    piece_final_x: int = Field(ge=0, le=400)


class RegisterRequest(SlideCaptchaProof):
    email: EmailStr
    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def strip_username(cls, v: str) -> str:
        return (v or "").strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_rule(v)


class LoginRequest(SlideCaptchaProof):
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
    captcha_id: str = Field(min_length=8, max_length=128)
    captcha_answer: int = Field(ge=0, le=99)


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


class SlideCaptchaIssueResponse(BaseModel):
    captcha_id: str
    image_base64: str
    piece_image_base64: str
    scene_width: int
    scene_height: int


class MathCaptchaIssueResponse(BaseModel):
    captcha_id: str
    left: int
    right: int


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password_rule(v)


class UpdateAvatarRequest(BaseModel):
    avatar_url: str = Field(min_length=1, max_length=2000000)


class NotificationPreferencesResponse(BaseModel):
    notify_email: bool
    notify_browser: bool
    notify_marketing: bool
    updated_at: datetime


class UpdateNotificationPreferencesRequest(BaseModel):
    notify_email: bool
    notify_browser: bool
    notify_marketing: bool


class TranslationCompletedNotifyRequest(BaseModel):
    title: str = Field(default="文档翻译", min_length=1, max_length=255)
    document_count: int = Field(default=1, ge=1, le=100)
    word_count: int = Field(default=0, ge=0, le=2000000)
    file_size_bytes: int = Field(default=0, ge=0, le=2000000000)


class DeleteAccountRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    confirm_text: str = Field(min_length=6, max_length=32)


class UserPreferencesResponse(BaseModel):
    preferred_target_language: str
    ui_language: str
    auto_save_history: bool
    enable_shortcuts: bool
    updated_at: datetime


class UpdateUserPreferencesRequest(BaseModel):
    preferred_target_language: str = Field(min_length=2, max_length=32)
    ui_language: str = Field(min_length=2, max_length=16)
    auto_save_history: bool
    enable_shortcuts: bool


class UploadOutputPreferencesResponse(BaseModel):
    upload_size_limit_mb: int
    auto_import_provider: str
    default_output_format: str
    updated_at: datetime


class UpdateUploadOutputPreferencesRequest(BaseModel):
    upload_size_limit_mb: int = Field(ge=1, le=100)
    auto_import_provider: str = Field(min_length=2, max_length=32)
    default_output_format: str = Field(min_length=2, max_length=16)


class PrivacySettingsResponse(BaseModel):
    data_retention_days: int
    updated_at: datetime


class UpdatePrivacySettingsRequest(BaseModel):
    data_retention_days: int


class ApiKeyItemResponse(BaseModel):
    id: str
    masked_key: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


class ApiKeyCreateResponse(BaseModel):
    id: str
    raw_key: str
    masked_key: str
    created_at: datetime


class DocumentItemResponse(BaseModel):
    id: str
    file_name: str
    created_at: datetime
    mime_type: str
    file_size_bytes: int
    document_count: int
    word_count: int
    status: str
    has_original_file: bool = False
    has_translated_file: bool = False


class DocumentMetaResponse(BaseModel):
    id: str
    page_count: int

