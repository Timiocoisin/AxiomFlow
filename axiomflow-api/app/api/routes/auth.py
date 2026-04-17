from __future__ import annotations

import base64
import json
import logging
import re
from urllib.parse import quote, urlencode
from urllib.request import Request as UrlRequest
from urllib.request import urlopen
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
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
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.translation_activity import TranslationActivity
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


router = APIRouter()
logger = logging.getLogger("axiomflow.oauth")
MAX_AVATAR_URL_LEN = 2_000_000

_UNAME_CLEAN_RE = re.compile(r"[^a-zA-Z0-9_]+")


def _require_slide(*, captcha_id: str, piece_final_x: int) -> None:
    if not validate_and_consume_slide(captcha_id=captcha_id, piece_final_x=piece_final_x):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_slide_captcha")


def _require_math(*, captcha_id: str, answer: int) -> None:
    if not validate_and_consume_math(captcha_id=captcha_id, answer=answer):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_math_captcha")


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
    title = (payload.title or "文档翻译").strip()[:255] or "文档翻译"

    act = TranslationActivity(
        user_id=user.id,
        title=title,
        document_count=doc_count,
        word_count=word_count,
    )
    db.add(act)
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
        recent.append(
            {
                "title": f"{(title or '翻译文档')[:80]}（{int(document_count or 0)} 份）",
                "time": created_at.isoformat(),
                "status": "translated",
                "ip": f"{int(word_count or 0)} 字",
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
                "title": "发起了密码重置请求",
                "time": created_at.isoformat(),
                "status": "password_reset",
                "ip": "-",
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
                "title": "完成了邮箱验证",
                "time": used_at.isoformat(),
                "status": "email_verified",
                "ip": "-",
            }
        )

    if user.last_login_at:
        recent.append(
            {
                "title": "登录了账户",
                "time": user.last_login_at.isoformat(),
                "status": "login",
                "ip": "-",
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
    db.execute(delete(User).where(User.id == user.id))
    db.commit()

    settings = get_settings()
    response.delete_cookie(key=settings.REFRESH_COOKIE_NAME, path=settings.REFRESH_COOKIE_PATH)
    return OkResponse(ok=True)
