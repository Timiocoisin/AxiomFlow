from __future__ import annotations

import base64
import io
import json
import logging
import mimetypes
import re
import uuid
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request as UrlRequest
from urllib.request import urlopen
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.limiter import limiter
from app.core.security import (
    create_access_token,
    hash_password,
    new_code_raw,
    new_token_raw,
    now_utc,
    token_sha256,
    verify_password,
)
from app.db.session import get_db
from app.models.email_token import EmailVerificationToken
from app.models.api_key import ApiKey
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.translation_activity import TranslationActivity
from app.models.user_document import UserDocument
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    MathCaptchaIssueResponse,
    OkResponse,
    RegisterRequest,
    RequestPasswordResetRequest,
    UpdateNotificationPreferencesRequest,
    TranslationCompletedNotifyRequest,
    DeleteAccountRequest,
    UpdateUserPreferencesRequest,
    UserPreferencesResponse,
    UpdateUploadOutputPreferencesRequest,
    UploadOutputPreferencesResponse,
    PrivacySettingsResponse,
    UpdatePrivacySettingsRequest,
    ApiKeyItemResponse,
    ApiKeyCreateResponse,
    DocumentItemResponse,
    DocumentMetaResponse,
    NotificationPreferencesResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    SlideCaptchaIssueResponse,
    TokenResponse,
    UpdateAvatarRequest,
    VerifyEmailRequest,
)
from app.services.mailer import send_password_reset_email, send_verification_email
from app.services.mailer import send_security_alert_email, send_translation_completed_email
from app.services.math_captcha import issue_math_challenge, validate_and_consume_math
from app.services.oauth_state import consume_oauth_state, issue_oauth_state
from app.services.slide_captcha import issue_slide_challenge, validate_and_consume_slide
from pypdf import PdfReader


router = APIRouter()
logger = logging.getLogger("axiomflow.oauth")
MAX_AVATAR_URL_LEN = 2_000_000

_UNAME_CLEAN_RE = re.compile(r"[^a-zA-Z0-9_]+")
_DOC_STORAGE_ROOT = Path(__file__).resolve().parents[3] / "storage" / "documents"


def _require_slide(*, captcha_id: str, piece_final_x: int) -> None:
    if not validate_and_consume_slide(captcha_id=captcha_id, piece_final_x=piece_final_x):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_slide_captcha")


def _require_math(*, captcha_id: str, answer: int) -> None:
    if not validate_and_consume_math(captcha_id=captcha_id, answer=answer):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_math_captcha")


def _safe_filename(name: str) -> str:
    base = Path(name or "").name.strip() or "uploaded-file.pdf"
    base = re.sub(r"[^\w\-.()\[\] ]+", "_", base)
    return base[:255]


def _document_abs_path_or_404(*, rel_path: str) -> Path:
    rel = (rel_path or "").strip()
    if not rel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document_file_not_found")
    abs_path = (_DOC_STORAGE_ROOT / rel).resolve()
    root_abs = _DOC_STORAGE_ROOT.resolve()
    if root_abs not in abs_path.parents and abs_path != root_abs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_document_path")
    if not abs_path.exists() or not abs_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document_file_not_found")
    return abs_path


def _document_abs_path_or_none(*, rel_path: str) -> Path | None:
    rel = (rel_path or "").strip()
    if not rel:
        return None
    abs_path = (_DOC_STORAGE_ROOT / rel).resolve()
    root_abs = _DOC_STORAGE_ROOT.resolve()
    if root_abs not in abs_path.parents and abs_path != root_abs:
        return None
    if not abs_path.exists() or not abs_path.is_file():
        return None
    return abs_path


def _oauth_callback_url(provider: str) -> str:
    s = get_settings()
    return f"{s.PUBLIC_API_URL.rstrip('/')}/auth/oauth/{provider}/callback"


def _frontend_oauth_result_redirect(
    *,
    oauth_done: bool = False,
    error: str | None = None,
) -> str:
    s = get_settings()
    base = f"{s.PUBLIC_WEB_URL.rstrip('/')}/#/auth"
    params = []
    if oauth_done:
        params.append("oauth_done=1")
    if error:
        params.append(f"oauth_error={quote(error)}")
    return f"{base}?{'&'.join(params)}" if params else base


def _http_post_form_json(url: str, form_data: dict[str, str], headers: dict[str, str] | None = None) -> dict:
    payload = urlencode(form_data).encode("utf-8")
    req = UrlRequest(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Accept", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    with urlopen(req, timeout=12) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_get_json(url: str, headers: dict[str, str] | None = None):
    req = UrlRequest(url, method="GET")
    req.add_header("Accept", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    with urlopen(req, timeout=12) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_avatar_data_uri(url: str | None) -> str:
    """
    Fetch remote avatar and convert to data URI so frontend can render it
    even when third-party image hosts are blocked in the user's network.
    """
    u = (url or "").strip()
    if not u.startswith("http"):
        return ""
    try:
        req = UrlRequest(
            u,
            headers={
                "User-Agent": "AxiomFlow-OAuth/1.0",
                "Accept": "image/*,*/*;q=0.8",
            },
            method="GET",
        )
        with urlopen(req, timeout=10) as resp:
            ctype = str(resp.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
            raw = resp.read(1024 * 1024)  # cap to 1MB for avatar
        if not ctype.startswith("image/") or not raw:
            return ""
        b64 = base64.b64encode(raw).decode("ascii")
        data_uri = f"data:{ctype};base64,{b64}"
        if len(data_uri) > MAX_AVATAR_URL_LEN:
            return ""
        return data_uri
    except Exception:
        return ""


def _choose_avatar_for_storage(*, avatar_data_uri: str, avatar_hint: str) -> str | None:
    # Prefer embedded avatar for better reliability, but never exceed DB-safe length.
    preferred = (avatar_data_uri or "").strip()
    fallback = (avatar_hint or "").strip()
    if preferred and len(preferred) <= MAX_AVATAR_URL_LEN:
        return preferred
    if fallback and len(fallback) <= MAX_AVATAR_URL_LEN:
        return fallback
    return None


def _derive_unique_username(db: Session, email: str) -> str:
    local = (email.split("@", 1)[0] if "@" in email else email).strip().lower()
    base = _UNAME_CLEAN_RE.sub("_", local).strip("_") or "user"
    base = base[:50]
    candidate = base
    i = 0
    while db.scalar(select(User).where(User.username == candidate)):
        i += 1
        candidate = f"{base}_{i}"
        if len(candidate) > 64:
            candidate = candidate[:64]
    return candidate


def _ua_to_device_label(ua: str | None) -> str:
    text = (ua or "").lower()
    if not text:
        return "Unknown device"
    browser = "Browser"
    if "edg/" in text:
        browser = "Edge"
    elif "chrome/" in text and "edg/" not in text:
        browser = "Chrome"
    elif "firefox/" in text:
        browser = "Firefox"
    elif "safari/" in text and "chrome/" not in text:
        browser = "Safari"

    os_name = "Unknown OS"
    if "windows" in text:
        os_name = "Windows"
    elif "mac os x" in text or "macintosh" in text:
        os_name = "macOS"
    elif "android" in text:
        os_name = "Android"
    elif "iphone" in text or "ipad" in text or "ios" in text:
        os_name = "iOS"
    elif "linux" in text:
        os_name = "Linux"
    return f"{browser} on {os_name}"


def _mask_api_key(*, key_prefix: str, key_last4: str) -> str:
    return f"{key_prefix}{'*' * 20}{key_last4}"


def _issue_login_response_for_user(*, request: Request, db: Session, user: User) -> tuple[TokenResponse, str]:
    pair = create_access_token(subject=user.id, extra={"email": user.email})

    settings = get_settings()
    refresh_raw = new_token_raw()
    refresh_hash = token_sha256(refresh_raw)
    refresh = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=now_utc() + timedelta(seconds=settings.JWT_REFRESH_TTL_SECONDS),
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    db.add(refresh)
    user.last_login_at = now_utc()
    db.commit()

    return TokenResponse(access_token=pair.access_token, access_expires_at=pair.access_expires_at), refresh_raw


@router.get("/_ping")
def auth_ping() -> dict:
    return {"ok": True}


@router.get("/oauth/{provider}/start")
@limiter.limit("20/minute")
def oauth_start(provider: str, request: Request):
    provider = (provider or "").lower().strip()
    s = get_settings()
    state = issue_oauth_state(provider)

    if provider == "google":
        if not s.OAUTH_GOOGLE_CLIENT_ID or not s.OAUTH_GOOGLE_CLIENT_SECRET:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="google_oauth_not_configured")
        q = urlencode(
            {
                "client_id": s.OAUTH_GOOGLE_CLIENT_ID,
                "redirect_uri": _oauth_callback_url("google"),
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "prompt": "select_account",
            }
        )
        return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{q}", status_code=302)

    if provider == "github":
        if not s.OAUTH_GITHUB_CLIENT_ID or not s.OAUTH_GITHUB_CLIENT_SECRET:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="github_oauth_not_configured")
        q = urlencode(
            {
                "client_id": s.OAUTH_GITHUB_CLIENT_ID,
                "redirect_uri": _oauth_callback_url("github"),
                "scope": "read:user user:email",
                "state": state,
            }
        )
        return RedirectResponse(f"https://github.com/login/oauth/authorize?{q}", status_code=302)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unsupported_oauth_provider")


@router.get("/oauth/{provider}/callback")
@limiter.limit("30/minute")
def oauth_callback(provider: str, request: Request, code: str = "", state: str = "", db: Session = Depends(get_db)):
    provider = (provider or "").lower().strip()
    if not code or not state or not consume_oauth_state(state, provider):
        return RedirectResponse(_frontend_oauth_result_redirect(error="invalid_oauth_state"), status_code=302)

    s = get_settings()
    try:
        email_verified_from_provider = False
        oauth_verified = True
        if provider == "google":
            token_json = _http_post_form_json(
                "https://oauth2.googleapis.com/token",
                {
                    "code": code,
                    "client_id": s.OAUTH_GOOGLE_CLIENT_ID,
                    "client_secret": s.OAUTH_GOOGLE_CLIENT_SECRET,
                    "redirect_uri": _oauth_callback_url("google"),
                    "grant_type": "authorization_code",
                },
            )
            access = token_json.get("access_token")
            if not access:
                raise ValueError("missing_access_token")
            profile = _http_get_json(
                "https://openidconnect.googleapis.com/v1/userinfo",
                {"Authorization": f"Bearer {access}"},
            )
            email = str(profile.get("email") or "").strip().lower()
            if not email:
                raise ValueError("missing_email")
            email_verified_from_provider = bool(profile.get("email_verified"))
            username_hint = str(profile.get("name") or profile.get("given_name") or "").strip()
            avatar_hint = str(profile.get("picture") or "").strip()
            avatar_data_uri = _fetch_avatar_data_uri(avatar_hint)

        elif provider == "github":
            token_json = _http_post_form_json(
                "https://github.com/login/oauth/access_token",
                {
                    "code": code,
                    "client_id": s.OAUTH_GITHUB_CLIENT_ID,
                    "client_secret": s.OAUTH_GITHUB_CLIENT_SECRET,
                    "redirect_uri": _oauth_callback_url("github"),
                },
            )
            access = token_json.get("access_token")
            if not access:
                raise ValueError("missing_access_token")
            profile = _http_get_json("https://api.github.com/user", {"Authorization": f"Bearer {access}"})
            emails = _http_get_json("https://api.github.com/user/emails", {"Authorization": f"Bearer {access}"})
            email = ""
            github_email_verified = False
            profile_email = str(profile.get("email") or "").strip().lower()
            if profile_email:
                email = profile_email
            if isinstance(emails, list):
                primary = next((e for e in emails if isinstance(e, dict) and e.get("primary") and e.get("verified")), None)
                if not primary:
                    primary = next((e for e in emails if isinstance(e, dict) and e.get("verified")), None)
                if not primary:
                    primary = next((e for e in emails if isinstance(e, dict) and e.get("primary")), None)
                if not primary:
                    primary = next((e for e in emails if isinstance(e, dict) and e.get("email")), None)
                if primary:
                    email = str(primary.get("email") or "").strip().lower()
                    github_email_verified = bool(primary.get("verified"))
            if not email:
                login_name = str(profile.get("login") or "").strip().lower()
                if login_name:
                    email = f"{login_name}@users.noreply.github.com"
                else:
                    uid = str(profile.get("id") or "").strip()
                    if uid:
                        email = f"github_{uid}@users.noreply.github.com"
            if not email:
                raise ValueError("github_email_unavailable")
            # GitHub noreply addresses are identity placeholders; treat as OAuth-verified
            # but not "contactable email verified".
            email_verified_from_provider = github_email_verified and not email.endswith("@users.noreply.github.com")
            username_hint = str(profile.get("name") or profile.get("login") or "").strip()
            avatar_hint = str(profile.get("avatar_url") or "").strip()
            avatar_data_uri = _fetch_avatar_data_uri(avatar_hint)

        else:
            return RedirectResponse(_frontend_oauth_result_redirect(error="unsupported_oauth_provider"), status_code=302)

        user = db.scalar(select(User).where(User.email == email))
        if not user:
            uname = _UNAME_CLEAN_RE.sub("_", username_hint).strip("_")[:64] if username_hint else ""
            if not uname or len(uname) < 2:
                uname = _derive_unique_username(db, email)
            if db.scalar(select(User).where(User.username == uname)):
                uname = _derive_unique_username(db, email)
            user = User(
                email=email,
                username=uname,
                avatar_url=_choose_avatar_for_storage(avatar_data_uri=avatar_data_uri, avatar_hint=avatar_hint),
                password_hash=hash_password(new_token_raw(24)),
                is_email_verified=email_verified_from_provider,
                is_oauth_verified=oauth_verified,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            changed = False
            if oauth_verified and not user.is_oauth_verified:
                user.is_oauth_verified = True
                changed = True
            if email_verified_from_provider and not user.is_email_verified:
                user.is_email_verified = True
                changed = True
            merged_avatar = _choose_avatar_for_storage(avatar_data_uri=avatar_data_uri, avatar_hint=avatar_hint)
            if merged_avatar and user.avatar_url != merged_avatar:
                user.avatar_url = merged_avatar
                changed = True
            if changed:
                db.commit()

        _, refresh_raw = _issue_login_response_for_user(request=request, db=db, user=user)
        rr = RedirectResponse(
            _frontend_oauth_result_redirect(oauth_done=True),
            status_code=302,
        )
        rr.set_cookie(
            key=s.REFRESH_COOKIE_NAME,
            value=refresh_raw,
            httponly=True,
            secure=s.REFRESH_COOKIE_SECURE,
            samesite=s.REFRESH_COOKIE_SAMESITE,
            path=s.REFRESH_COOKIE_PATH,
            max_age=s.JWT_REFRESH_TTL_SECONDS,
        )
        return rr
    except ValueError as e:
        logger.warning("oauth_callback_value_error provider=%s detail=%s", provider, str(e))
        return RedirectResponse(_frontend_oauth_result_redirect(error=str(e)), status_code=302)
    except Exception:
        logger.exception("oauth_callback_failed provider=%s", provider)
        return RedirectResponse(_frontend_oauth_result_redirect(error="oauth_login_failed"), status_code=302)


@router.get("/me")
@limiter.limit("120/minute")
def me(request: Request, user: User = Depends(get_current_user)) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "avatar_url": user.avatar_url,
        "is_email_verified": user.is_email_verified,
        "is_oauth_verified": user.is_oauth_verified,
    }


@router.get("/notification-preferences", response_model=NotificationPreferencesResponse)
@limiter.limit("120/minute")
def get_notification_preferences(request: Request, user: User = Depends(get_current_user)) -> NotificationPreferencesResponse:
    return NotificationPreferencesResponse(
        notify_email=bool(user.notify_email),
        notify_browser=bool(user.notify_browser),
        notify_marketing=bool(user.notify_marketing),
        updated_at=user.updated_at,
    )


@router.put("/notification-preferences", response_model=NotificationPreferencesResponse)
@limiter.limit("60/minute")
def update_notification_preferences(
    request: Request,
    payload: UpdateNotificationPreferencesRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationPreferencesResponse:
    user.notify_email = bool(payload.notify_email)
    user.notify_browser = bool(payload.notify_browser)
    user.notify_marketing = bool(payload.notify_marketing)
    db.commit()
    db.refresh(user)
    return NotificationPreferencesResponse(
        notify_email=bool(user.notify_email),
        notify_browser=bool(user.notify_browser),
        notify_marketing=bool(user.notify_marketing),
        updated_at=user.updated_at,
    )


@router.get("/preferences", response_model=UserPreferencesResponse)
@limiter.limit("120/minute")
def get_user_preferences(request: Request, user: User = Depends(get_current_user)) -> UserPreferencesResponse:
    return UserPreferencesResponse(
        preferred_target_language=(user.preferred_target_language or "zh-CN"),
        ui_language=(user.ui_language or "zh-CN"),
        auto_save_history=bool(user.auto_save_history),
        enable_shortcuts=bool(user.enable_shortcuts),
        updated_at=user.updated_at,
    )


@router.put("/preferences", response_model=UserPreferencesResponse)
@limiter.limit("60/minute")
def update_user_preferences(
    request: Request,
    payload: UpdateUserPreferencesRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPreferencesResponse:
    target = (payload.preferred_target_language or "").strip()
    ui = (payload.ui_language or "").strip()
    allowed_langs = {"zh-CN", "en-US"}
    if target not in allowed_langs or ui not in allowed_langs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_language_code")
    user.preferred_target_language = target
    user.ui_language = ui
    user.auto_save_history = bool(payload.auto_save_history)
    user.enable_shortcuts = bool(payload.enable_shortcuts)
    db.commit()
    db.refresh(user)
    return UserPreferencesResponse(
        preferred_target_language=(user.preferred_target_language or "zh-CN"),
        ui_language=(user.ui_language or "zh-CN"),
        auto_save_history=bool(user.auto_save_history),
        enable_shortcuts=bool(user.enable_shortcuts),
        updated_at=user.updated_at,
    )


@router.get("/upload-output-preferences", response_model=UploadOutputPreferencesResponse)
@limiter.limit("120/minute")
def get_upload_output_preferences(request: Request, user: User = Depends(get_current_user)) -> UploadOutputPreferencesResponse:
    return UploadOutputPreferencesResponse(
        upload_size_limit_mb=int(user.upload_size_limit_mb or 20),
        auto_import_provider=(user.auto_import_provider or "none"),
        default_output_format=(user.default_output_format or "pdf"),
        updated_at=user.updated_at,
    )


@router.put("/upload-output-preferences", response_model=UploadOutputPreferencesResponse)
@limiter.limit("60/minute")
def update_upload_output_preferences(
    request: Request,
    payload: UpdateUploadOutputPreferencesRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadOutputPreferencesResponse:
    allowed_sizes = {20, 50, 100}
    allowed_providers = {"none", "google_drive"}
    allowed_formats = {"pdf", "docx", "txt"}
    if int(payload.upload_size_limit_mb) not in allowed_sizes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_upload_size_limit")
    if payload.auto_import_provider not in allowed_providers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_auto_import_provider")
    if payload.default_output_format not in allowed_formats:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_default_output_format")

    user.upload_size_limit_mb = int(payload.upload_size_limit_mb)
    user.auto_import_provider = payload.auto_import_provider
    user.default_output_format = payload.default_output_format
    db.commit()
    db.refresh(user)
    return UploadOutputPreferencesResponse(
        upload_size_limit_mb=int(user.upload_size_limit_mb or 20),
        auto_import_provider=(user.auto_import_provider or "none"),
        default_output_format=(user.default_output_format or "pdf"),
        updated_at=user.updated_at,
    )


@router.get("/privacy-settings", response_model=PrivacySettingsResponse)
@limiter.limit("120/minute")
def get_privacy_settings(request: Request, user: User = Depends(get_current_user)) -> PrivacySettingsResponse:
    return PrivacySettingsResponse(
        data_retention_days=int(user.data_retention_days if user.data_retention_days is not None else 7),
        updated_at=user.updated_at,
    )


@router.put("/privacy-settings", response_model=PrivacySettingsResponse)
@limiter.limit("60/minute")
def update_privacy_settings(
    request: Request,
    payload: UpdatePrivacySettingsRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PrivacySettingsResponse:
    allowed = {-1, 0, 1, 7, 30}
    if int(payload.data_retention_days) not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_data_retention_days")
    user.data_retention_days = int(payload.data_retention_days)
    db.commit()
    db.refresh(user)
    return PrivacySettingsResponse(
        data_retention_days=int(user.data_retention_days if user.data_retention_days is not None else 7),
        updated_at=user.updated_at,
    )


@router.get("/api-keys", response_model=list[ApiKeyItemResponse])
@limiter.limit("120/minute")
def list_api_keys(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ApiKeyItemResponse]:
    rows = db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == user.id)
        .order_by(ApiKey.created_at.desc())
        .limit(100)
    ).scalars().all()
    return [
        ApiKeyItemResponse(
            id=row.id,
            masked_key=_mask_api_key(key_prefix=row.key_prefix, key_last4=row.key_last4),
            created_at=row.created_at,
            last_used_at=row.last_used_at,
            revoked_at=row.revoked_at,
        )
        for row in rows
    ]


@router.post("/api-keys", response_model=ApiKeyCreateResponse)
@limiter.limit("20/minute")
def create_api_key(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiKeyCreateResponse:
    raw = f"sk-trans-{new_token_raw(24)}"
    key = ApiKey(
        user_id=user.id,
        key_hash=token_sha256(raw),
        key_prefix=raw[:9],
        key_last4=raw[-4:],
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return ApiKeyCreateResponse(
        id=key.id,
        raw_key=raw,
        masked_key=_mask_api_key(key_prefix=key.key_prefix, key_last4=key.key_last4),
        created_at=key.created_at,
    )


@router.delete("/api-keys/{api_key_id}", response_model=OkResponse)
@limiter.limit("60/minute")
def revoke_api_key(
    api_key_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OkResponse:
    key = db.scalar(select(ApiKey).where(ApiKey.id == api_key_id, ApiKey.user_id == user.id))
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="api_key_not_found")
    if key.revoked_at is None:
        key.revoked_at = now_utc()
        db.commit()
    return OkResponse(ok=True)


@router.post("/notify/translation-completed", response_model=OkResponse)
@limiter.limit("30/minute")
def notify_translation_completed(
    request: Request,
    payload: TranslationCompletedNotifyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OkResponse:
    doc_count = int(payload.document_count or 0)
    word_count = int(payload.word_count or 0)
    file_size_bytes = int(payload.file_size_bytes or 0)
    title = (payload.title or "文档翻译").strip()[:255] or "文档翻译"

    act = TranslationActivity(
        user_id=user.id,
        title=title,
        document_count=doc_count,
        word_count=word_count,
    )
    db.add(act)
    db.add(
        UserDocument(
            user_id=user.id,
            file_name=title,
            file_size_bytes=max(0, file_size_bytes),
            word_count=word_count,
            status="completed",
        )
    )
    user.translated_documents = int(user.translated_documents or 0) + doc_count
    user.translated_words = int(user.translated_words or 0) + word_count
    db.commit()

    if user.notify_email:
        try:
            send_translation_completed_email(
                to_email=user.email,
                title=title,
                document_count=doc_count,
                word_count=word_count,
            )
        except Exception:
            logger.warning("send_translation_completed_email_failed user=%s", user.id, exc_info=True)
    return OkResponse(ok=True)


@router.get("/profile/stats")
@limiter.limit("120/minute")
def profile_stats(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    now = now_utc()
    last_7_days = [(now - timedelta(days=d)).date() for d in range(6, -1, -1)]
    cutoff = datetime.combine(last_7_days[0], datetime.min.time(), tzinfo=now.tzinfo)

    activity_rows = db.execute(
        select(
            TranslationActivity.created_at,
            TranslationActivity.document_count,
            TranslationActivity.word_count,
            TranslationActivity.title,
        )
        .where(TranslationActivity.user_id == user.id, TranslationActivity.created_at >= cutoff)
        .order_by(TranslationActivity.created_at.desc())
    ).all()
    daily_count: dict = {d: 0 for d in last_7_days}
    for created_at, document_count, _, _ in activity_rows:
        day = created_at.date()
        if day in daily_count:
            daily_count[day] += int(document_count or 0)

    chart = [{"date": d.strftime("%m-%d"), "count": int(daily_count[d])} for d in last_7_days]

    recent: list[dict] = []
    for created_at, document_count, word_count, title in activity_rows[:6]:
        doc_count = int(document_count or 0)
        words = int(word_count or 0)
        recent.append(
            {
                "title": (title or "Untitled document")[:80],
                "time": created_at.isoformat(),
                "status": "translated",
                "ip": "-",
                "activity_key": "translation_completed",
                "document_count": doc_count,
                "word_count": words,
            }
        )
    reset_rows = db.execute(
        select(PasswordResetToken.created_at)
        .where(PasswordResetToken.user_id == user.id)
        .order_by(PasswordResetToken.created_at.desc())
        .limit(4)
    ).all()
    for (created_at,) in reset_rows:
        recent.append(
            {
                "title": "password_reset_requested",
                "time": created_at.isoformat(),
                "status": "password_reset",
                "ip": "-",
                "activity_key": "password_reset_requested",
            }
        )

    verify_rows = db.execute(
        select(EmailVerificationToken.used_at)
        .where(EmailVerificationToken.user_id == user.id, EmailVerificationToken.used_at.is_not(None))
        .order_by(EmailVerificationToken.used_at.desc())
        .limit(2)
    ).all()
    for (used_at,) in verify_rows:
        if used_at is None:
            continue
        recent.append(
            {
                "title": "email_verified",
                "time": used_at.isoformat(),
                "status": "email_verified",
                "ip": "-",
                "activity_key": "email_verified",
            }
        )

    if user.last_login_at:
        recent.append(
            {
                "title": "login_succeeded",
                "time": user.last_login_at.isoformat(),
                "status": "login",
                "ip": "-",
                "activity_key": "login_succeeded",
            }
        )
    recent = sorted(recent, key=lambda x: x["time"], reverse=True)[:10]

    login_history_rows = db.execute(
        select(RefreshToken.created_at, RefreshToken.user_agent, RefreshToken.ip, RefreshToken.revoked_at)
        .where(RefreshToken.user_id == user.id)
        .order_by(RefreshToken.created_at.desc())
        .limit(50)
    ).all()
    login_history: list[dict] = []
    seen: set[tuple[str, str, str, str]] = set()
    online_marked = False
    for created_at, ua, ip, revoked_at in login_history_rows:
        device = _ua_to_device_label(ua)
        ip_text = ip or "-"
        minute_bucket = created_at.strftime("%Y-%m-%d %H:%M")
        status = "online" if revoked_at is None else "expired"
        dedupe_key = (device, ip_text, minute_bucket, status)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        if status == "online" and not online_marked:
            status = "online_current"
            online_marked = True

        login_history.append(
            {
                "device": device,
                "ip": ip_text,
                "time": created_at.isoformat(),
                "status": status,
            }
        )
        if len(login_history) >= 8:
            break

    last_month_start = (now - timedelta(days=60)).date()
    month_boundary = (now - timedelta(days=30)).date()
    counts = db.execute(
        select(func.date(TranslationActivity.created_at).label("d"), func.sum(TranslationActivity.document_count))
        .where(
            TranslationActivity.user_id == user.id,
            TranslationActivity.created_at >= datetime.combine(last_month_start, datetime.min.time(), tzinfo=now.tzinfo),
        )
        .group_by(func.date(TranslationActivity.created_at))
    ).all()
    prev_count = sum(int(c) for d, c in counts if d < month_boundary)
    cur_count = sum(int(c) for d, c in counts if d >= month_boundary)
    month_delta_pct = 0
    if prev_count > 0:
        month_delta_pct = int(round(((cur_count - prev_count) / prev_count) * 100))
    elif cur_count > 0:
        month_delta_pct = 100

    total_docs = int(
        db.scalar(select(func.coalesce(func.sum(TranslationActivity.document_count), 0)).where(TranslationActivity.user_id == user.id))
        or 0
    )
    total_words = int(
        db.scalar(select(func.coalesce(func.sum(TranslationActivity.word_count), 0)).where(TranslationActivity.user_id == user.id))
        or 0
    )
    hours_saved = int(round((total_words / 600.0)))

    return {
        "metrics": {
            "translated_documents": total_docs,
            "translated_words": total_words,
            "credits_balance": int(user.credits_balance or 0),
            "month_delta_pct": month_delta_pct,
            "hours_saved": hours_saved,
        },
        "activity_chart": chart,
        "recent_activities": recent,
        "login_history": login_history,
    }


@router.get("/documents", response_model=list[DocumentItemResponse])
@limiter.limit("120/minute")
def list_documents(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[DocumentItemResponse]:
    rows = db.execute(
        select(
            UserDocument.id,
            UserDocument.file_name,
            UserDocument.created_at,
            UserDocument.mime_type,
            UserDocument.original_storage_path,
            UserDocument.file_size_bytes,
            UserDocument.word_count,
            UserDocument.status,
            UserDocument.translated_storage_path,
        )
        .where(UserDocument.user_id == user.id)
        .order_by(UserDocument.created_at.desc())
        .limit(200)
    ).all()

    return [
        DocumentItemResponse(
            id=row_id,
            file_name=(file_name or "Untitled document")[:255],
            created_at=created_at,
            mime_type=(mime_type or "application/octet-stream"),
            file_size_bytes=int(file_size_bytes or 0),
            document_count=1,
            word_count=int(word_count or 0),
            status=(status_text or "completed"),
            has_original_file=bool(_document_abs_path_or_none(rel_path=original_storage_path or "")),
            has_translated_file=bool(translated_storage_path),
        )
        for row_id, file_name, created_at, mime_type, original_storage_path, file_size_bytes, word_count, status_text, translated_storage_path in rows
    ]


@router.post("/documents/upload", response_model=DocumentItemResponse)
@limiter.limit("30/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentItemResponse:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty_file")
    if len(raw) > 100 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="file_too_large")

    safe_name = _safe_filename(file.filename or "uploaded-file.pdf")
    ext = Path(safe_name).suffix or ".bin"
    rel_path = Path(user.id) / f"{uuid.uuid4().hex}{ext}"
    abs_path = (_DOC_STORAGE_ROOT / rel_path).resolve()
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_bytes(raw)

    mime = (file.content_type or "").strip() or mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
    doc = UserDocument(
        user_id=user.id,
        file_name=safe_name,
        mime_type=mime,
        original_storage_path=str(rel_path).replace("\\", "/"),
        translated_storage_path=None,
        file_size_bytes=len(raw),
        word_count=0,
        status="completed",
    )
    db.add(doc)
    db.add(
        TranslationActivity(
            user_id=user.id,
            title=safe_name,
            document_count=1,
            word_count=0,
        )
    )
    user.translated_documents = int(user.translated_documents or 0) + 1
    db.commit()
    db.refresh(doc)

    return DocumentItemResponse(
        id=doc.id,
        file_name=doc.file_name,
        created_at=doc.created_at,
        mime_type=doc.mime_type,
        file_size_bytes=int(doc.file_size_bytes or 0),
        document_count=1,
        word_count=int(doc.word_count or 0),
        status=doc.status or "completed",
        has_translated_file=bool(doc.translated_storage_path),
    )


@router.get("/documents/{document_id}/meta", response_model=DocumentMetaResponse)
@limiter.limit("120/minute")
def document_meta(
    request: Request,
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentMetaResponse:
    row = db.scalar(select(UserDocument).where(UserDocument.id == document_id, UserDocument.user_id == user.id))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document_not_found")

    page_count = 1
    name = (row.file_name or "").lower()
    mime = (row.mime_type or "").lower()
    if name.endswith(".pdf") or "pdf" in mime:
        try:
            abs_path = _document_abs_path_or_404(rel_path=row.original_storage_path or "")
            reader = PdfReader(io.BytesIO(abs_path.read_bytes()))
            page_count = max(1, len(reader.pages))
        except HTTPException:
            raise
        except Exception:
            logger.warning("document_meta_page_count_failed id=%s", row.id, exc_info=True)
            page_count = 1

    return DocumentMetaResponse(id=row.id, page_count=page_count)


@router.get("/documents/{document_id}/download")
@limiter.limit("60/minute")
def download_document(
    request: Request,
    document_id: str,
    kind: str = Query("original"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.scalar(select(UserDocument).where(UserDocument.id == document_id, UserDocument.user_id == user.id))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document_not_found")

    if kind == "translated":
        rel = (row.translated_storage_path or "").strip()
        if not rel:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="translated_file_not_found")
    else:
        rel = (row.original_storage_path or "").strip()
        kind = "original"

    abs_path = _document_abs_path_or_404(rel_path=rel)

    out_name = row.file_name or "document.pdf"
    if kind == "translated":
        stem = Path(out_name).stem
        suffix = Path(out_name).suffix or ".pdf"
        out_name = f"{stem}.translated{suffix}"

    return FileResponse(
        path=str(abs_path),
        media_type=row.mime_type or "application/octet-stream",
        filename=out_name,
    )


@router.delete("/documents/{document_id}", response_model=OkResponse)
@limiter.limit("60/minute")
def delete_document(
    request: Request,
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OkResponse:
    row = db.scalar(select(UserDocument).where(UserDocument.id == document_id, UserDocument.user_id == user.id))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document_not_found")
    for rel in [(row.original_storage_path or "").strip(), (row.translated_storage_path or "").strip()]:
        if not rel:
            continue
        p = (_DOC_STORAGE_ROOT / rel).resolve()
        root_abs = _DOC_STORAGE_ROOT.resolve()
        if (root_abs in p.parents or p == root_abs) and p.exists() and p.is_file():
            try:
                p.unlink()
            except Exception:
                logger.warning("document_file_delete_failed path=%s", p, exc_info=True)
    db.delete(row)
    db.commit()
    return OkResponse(ok=True)


@router.post("/avatar", response_model=OkResponse)
@limiter.limit("30/minute")
def update_avatar(
    request: Request,
    payload: UpdateAvatarRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OkResponse:
    value = (payload.avatar_url or "").strip()
    if not value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_avatar_url")
    if len(value) > MAX_AVATAR_URL_LEN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="avatar_too_large")
    if not (value.startswith("data:image/") or value.startswith("http://") or value.startswith("https://")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_avatar_url")
    user.avatar_url = value
    db.commit()
    return OkResponse(ok=True)


@router.post("/captcha/slide-issue", response_model=SlideCaptchaIssueResponse)
@limiter.limit("30/minute")
def issue_slide_captcha(
    request: Request, scene_width: int = Query(320, ge=200, le=480), scene_height: int = Query(160, ge=120, le=220)
) -> SlideCaptchaIssueResponse:
    w = max(260, min(440, int(scene_width)))
    h = max(120, min(220, int(scene_height)))
    cid, hole_png, piece_png, rw, rh = issue_slide_challenge(scene_width=w, scene_height=h)
    b64 = base64.b64encode(hole_png).decode("ascii")
    piece_b64 = base64.b64encode(piece_png).decode("ascii")
    return SlideCaptchaIssueResponse(
        captcha_id=cid,
        image_base64=b64,
        piece_image_base64=piece_b64,
        scene_width=rw,
        scene_height=rh,
    )


@router.post("/captcha/math-issue", response_model=MathCaptchaIssueResponse)
@limiter.limit("30/minute")
def issue_math_captcha(request: Request) -> MathCaptchaIssueResponse:
    cid, a, b = issue_math_challenge()
    return MathCaptchaIssueResponse(captcha_id=cid, left=a, right=b)


@router.post("/register", response_model=OkResponse)
@limiter.limit("5/minute")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)) -> OkResponse:
    _require_slide(captcha_id=payload.captcha_id, piece_final_x=payload.piece_final_x)

    existing = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email_already_registered")

    name = payload.username
    taken_name = db.scalar(select(User).where(User.username == name))
    if taken_name:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username_taken")

    user = User(
        email=str(payload.email).lower(),
        username=name,
        password_hash=hash_password(payload.password),
        is_email_verified=False,
    )
    db.add(user)
    db.flush()

    token_raw = new_token_raw()
    token = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_sha256(token_raw),
        expires_at=now_utc() + timedelta(seconds=get_settings().EMAIL_VERIFY_TTL_SECONDS),
    )
    db.add(token)
    db.commit()

    try:
        send_verification_email(to_email=user.email, token=token_raw)
    except Exception:
        return OkResponse(ok=True, message="verification_email_send_failed")
    return OkResponse(ok=True, message="verification_email_queued")


@router.post("/login", response_model=TokenResponse)
@limiter.limit("20/minute")
def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    _require_slide(captcha_id=payload.captcha_id, piece_final_x=payload.piece_final_x)

    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    if not user.is_email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="email_not_verified")

    pair = create_access_token(subject=user.id, extra={"email": user.email})

    settings = get_settings()
    refresh_raw = new_token_raw()
    refresh_hash = token_sha256(refresh_raw)
    refresh = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=now_utc() + timedelta(seconds=settings.JWT_REFRESH_TTL_SECONDS),
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    db.add(refresh)
    user.last_login_at = now_utc()
    db.commit()

    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_raw,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
        max_age=settings.JWT_REFRESH_TTL_SECONDS,
    )
    return TokenResponse(access_token=pair.access_token, access_expires_at=pair.access_expires_at)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("60/minute")
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    settings = get_settings()
    raw = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_refresh_cookie")

    hashed = token_sha256(raw)
    token = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hashed,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now_utc(),
        )
    )
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token")

    user = db.scalar(select(User).where(User.id == token.user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token")

    token.revoked_at = now_utc()
    new_raw = new_token_raw()
    new_hash = token_sha256(new_raw)
    new_token = RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=now_utc() + timedelta(seconds=settings.JWT_REFRESH_TTL_SECONDS),
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    db.add(new_token)

    pair = create_access_token(subject=user.id, extra={"email": user.email})
    db.commit()

    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=new_raw,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
        max_age=settings.JWT_REFRESH_TTL_SECONDS,
    )
    return TokenResponse(access_token=pair.access_token, access_expires_at=pair.access_expires_at)


@router.post("/logout", response_model=OkResponse)
@limiter.limit("60/minute")
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> OkResponse:
    settings = get_settings()
    raw = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if raw:
        hashed = token_sha256(raw)
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == hashed, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now_utc())
        )
        db.commit()

    response.delete_cookie(key=settings.REFRESH_COOKIE_NAME, path=settings.REFRESH_COOKIE_PATH)
    return OkResponse(ok=True)


@router.post("/verify-email", response_model=TokenResponse)
@limiter.limit("30/minute")
def verify_email(
    request: Request,
    payload: VerifyEmailRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    hashed = token_sha256(payload.token)
    token = db.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == hashed,
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.expires_at > now_utc(),
        )
    )
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_or_expired_token")

    user = db.scalar(select(User).where(User.id == token.user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_or_expired_token")

    token.used_at = now_utc()
    user.is_email_verified = True
    pair = create_access_token(subject=user.id, extra={"email": user.email})

    settings = get_settings()
    refresh_raw = new_token_raw()
    refresh_hash = token_sha256(refresh_raw)
    refresh = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=now_utc() + timedelta(seconds=settings.JWT_REFRESH_TTL_SECONDS),
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    db.add(refresh)
    db.commit()

    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_raw,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
        max_age=settings.JWT_REFRESH_TTL_SECONDS,
    )
    return TokenResponse(access_token=pair.access_token, access_expires_at=pair.access_expires_at)


@router.post("/resend-verification", response_model=OkResponse)
@limiter.limit("5/minute")
def resend_verification(request: Request, payload: ResendVerificationRequest, db: Session = Depends(get_db)) -> OkResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or user.is_email_verified:
        return OkResponse(ok=True)

    token_raw = new_token_raw()
    token = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_sha256(token_raw),
        expires_at=now_utc() + timedelta(seconds=get_settings().EMAIL_VERIFY_TTL_SECONDS),
    )
    db.add(token)
    db.commit()

    try:
        send_verification_email(to_email=user.email, token=token_raw)
    except Exception:
        return OkResponse(ok=True, message="verification_email_send_failed")
    return OkResponse(ok=True, message="verification_email_queued")


@router.post("/request-password-reset", response_model=OkResponse)
@limiter.limit("5/minute")
def request_password_reset(
    request: Request, payload: RequestPasswordResetRequest, db: Session = Depends(get_db)
) -> OkResponse:
    _require_math(captcha_id=payload.captcha_id, answer=payload.captcha_answer)

    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user:
        return OkResponse(ok=True)

    token_raw = new_code_raw(6)
    token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_sha256(token_raw),
        expires_at=now_utc() + timedelta(seconds=get_settings().PASSWORD_RESET_TTL_SECONDS),
    )
    db.add(token)
    db.commit()

    try:
        send_password_reset_email(to_email=user.email, token=token_raw)
    except Exception:
        return OkResponse(ok=True, message="password_reset_email_send_failed")
    return OkResponse(ok=True, message="password_reset_email_queued")


@router.post("/reset-password", response_model=OkResponse)
@limiter.limit("10/minute")
def reset_password(request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> OkResponse:
    hashed = token_sha256(payload.token)
    token = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == hashed,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now_utc(),
        )
    )
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_or_expired_token")

    user = db.scalar(select(User).where(User.id == token.user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_or_expired_token")

    token.used_at = now_utc()
    user.password_hash = hash_password(payload.new_password)

    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now_utc())
    )
    db.commit()
    if user.notify_email:
        try:
            send_security_alert_email(to_email=user.email, event="密码已重置")
        except Exception:
            logger.warning("send_security_alert_email_failed user=%s event=reset_password", user.id, exc_info=True)
    return OkResponse(ok=True)


@router.post("/change-password", response_model=OkResponse)
@limiter.limit("10/minute")
def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OkResponse:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_current_password")

    user.password_hash = hash_password(payload.new_password)
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now_utc())
    )
    db.commit()
    if user.notify_email:
        try:
            send_security_alert_email(to_email=user.email, event="密码已修改")
        except Exception:
            logger.warning("send_security_alert_email_failed user=%s event=change_password", user.id, exc_info=True)
    return OkResponse(ok=True)


@router.get("/export-data")
@limiter.limit("10/minute")
def export_data(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    activities = db.execute(
        select(
            TranslationActivity.title,
            TranslationActivity.document_count,
            TranslationActivity.word_count,
            TranslationActivity.created_at,
        )
        .where(TranslationActivity.user_id == user.id)
        .order_by(TranslationActivity.created_at.desc())
        .limit(200)
    ).all()
    login_rows = db.execute(
        select(RefreshToken.created_at, RefreshToken.user_agent, RefreshToken.ip, RefreshToken.revoked_at)
        .where(RefreshToken.user_id == user.id)
        .order_by(RefreshToken.created_at.desc())
        .limit(100)
    ).all()
    return {
        "profile": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "avatar_url": user.avatar_url,
            "is_email_verified": bool(user.is_email_verified),
            "is_oauth_verified": bool(user.is_oauth_verified),
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        },
        "notification_preferences": {
            "notify_email": bool(user.notify_email),
            "notify_browser": bool(user.notify_browser),
            "notify_marketing": bool(user.notify_marketing),
        },
        "stats": {
            "translated_documents": int(user.translated_documents or 0),
            "translated_words": int(user.translated_words or 0),
            "credits_balance": int(user.credits_balance or 0),
        },
        "recent_translation_activities": [
            {
                "title": title,
                "document_count": int(document_count or 0),
                "word_count": int(word_count or 0),
                "time": created_at.isoformat(),
            }
            for title, document_count, word_count, created_at in activities
        ],
        "login_history": [
            {
                "time": created_at.isoformat(),
                "device": _ua_to_device_label(ua),
                "ip": ip or "-",
                "status": "online" if revoked_at is None else "expired",
            }
            for created_at, ua, ip, revoked_at in login_rows
        ],
        "exported_at": now_utc().isoformat(),
    }


@router.delete("/account", response_model=OkResponse)
@limiter.limit("5/minute")
def delete_account(
    request: Request,
    payload: DeleteAccountRequest,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OkResponse:
    if (payload.confirm_text or "").strip().upper() != "DELETE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_confirm_text")
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_current_password")

    db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
    db.execute(delete(EmailVerificationToken).where(EmailVerificationToken.user_id == user.id))
    db.execute(delete(TranslationActivity).where(TranslationActivity.user_id == user.id))
    db.execute(delete(ApiKey).where(ApiKey.user_id == user.id))
    db.execute(delete(User).where(User.id == user.id))
    db.commit()

    settings = get_settings()
    response.delete_cookie(key=settings.REFRESH_COOKIE_NAME, path=settings.REFRESH_COOKIE_PATH)
    return OkResponse(ok=True)
