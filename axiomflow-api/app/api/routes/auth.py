from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    hash_password,
    new_token_raw,
    new_code_raw,
    now_utc,
    token_sha256,
    verify_password,
)
from app.db.session import get_db
from app.models.email_token import EmailVerificationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    OkResponse,
    RegisterRequest,
    RequestPasswordResetRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.services.mailer import send_password_reset_email, send_verification_email


router = APIRouter()


@router.get("/_ping")
def auth_ping() -> dict:
    return {"ok": True}


@router.post("/register", response_model=OkResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> OkResponse:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email_already_registered")

    user = User(
        email=str(payload.email).lower(),
        username=payload.username,
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
        # token 已落库，用户可通过 resend 再次获取
        return OkResponse(ok=True, message="verification_email_send_failed")
    return OkResponse(ok=True, message="verification_email_queued")


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

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

    # Rotate refresh token (recommended)
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
def verify_email(
    payload: VerifyEmailRequest,
    request: Request,
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
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)) -> OkResponse:
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
def request_password_reset(
    payload: RequestPasswordResetRequest, db: Session = Depends(get_db)
) -> OkResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user:
        # avoid enumeration
        return OkResponse(ok=True)

    # 6-char human-enterable code (A-Z a-z 0-9)
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
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> OkResponse:
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

    # Revoke all refresh tokens for this user (recommended)
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now_utc())
    )
    db.commit()
    return OkResponse(ok=True)

