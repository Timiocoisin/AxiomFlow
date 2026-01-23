from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
from typing import Optional, List, Tuple

from ..core.user_db import get_db_session
from ..db.schema import (
    CaptchaSession,
    EmailCodeSession,
    PasswordResetToken,
    EmailVerifyToken,
    LoginAuditLog,
    PasswordHistory,
)


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def hash_code(code: str) -> str:
    """
    对验证码做 sha256（统一大写）避免明文落库。
    """
    normalized = (code or "").strip().upper()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# -------------------------
# Captcha sessions
# -------------------------


def upsert_captcha_session(session_id: str, code: str, *, expires_at: int, ip: str = "") -> None:
    with get_db_session() as session:
        obj = session.query(CaptchaSession).filter(CaptchaSession.session_id == session_id).first()
        if not obj:
            obj = CaptchaSession(
                session_id=session_id,
                code_hash=hash_code(code),
                ip=ip or "",
                expires_at=expires_at,
                created_at=_now_iso(),
            )
            session.add(obj)
        else:
            obj.code_hash = hash_code(code)
            obj.ip = ip or obj.ip or ""
            obj.expires_at = expires_at
        session.commit()


def verify_and_consume_captcha(session_id: str, code: str, *, now_ts: int) -> bool:
    with get_db_session() as session:
        obj = session.query(CaptchaSession).filter(CaptchaSession.session_id == session_id).first()
        if not obj:
            return False
        if now_ts > int(obj.expires_at):
            session.delete(obj)
            session.commit()
            return False
        if obj.code_hash != hash_code(code):
            return False
        session.delete(obj)  # 一次性使用
        session.commit()
        return True


# -------------------------
# Email code sessions (forgot password)
# -------------------------


def create_email_code_session(
    session_id: str,
    email: str,
    code: str,
    *,
    expires_at: int,
    ip: str = "",
) -> None:
    with get_db_session() as session:
        obj = EmailCodeSession(
            session_id=session_id,
            email=(email or "").lower(),
            code_hash=hash_code(code),
            ip=ip or "",
            expires_at=expires_at,
            created_at=_now_iso(),
        )
        session.add(obj)
        session.commit()


def verify_and_consume_email_code(
    session_id: str,
    email: str,
    code: str,
    *,
    now_ts: int,
) -> Tuple[bool, str]:
    """
    Returns: (ok, reason)
    """
    email_lower = (email or "").lower()
    with get_db_session() as session:
        obj = session.query(EmailCodeSession).filter(EmailCodeSession.session_id == session_id).first()
        if not obj:
            return False, "验证码已过期，请重新获取"
        if now_ts > int(obj.expires_at):
            session.delete(obj)
            session.commit()
            return False, "验证码已过期，请重新获取"
        if obj.email != email_lower:
            return False, "邮箱不匹配"
        if obj.code_hash != hash_code(code):
            return False, "验证码错误"
        session.delete(obj)  # 一次性使用
        session.commit()
        return True, ""


# -------------------------
# Password reset tokens
# -------------------------


def create_password_reset_token(token: str, email: str, *, expires_at: int, ip: str = "") -> None:
    with get_db_session() as session:
        obj = PasswordResetToken(
            token=token,
            email=(email or "").lower(),
            ip=ip or "",
            expires_at=expires_at,
            created_at=_now_iso(),
        )
        session.add(obj)
        session.commit()


def get_password_reset_token_email(token: str, *, now_ts: int) -> Optional[str]:
    with get_db_session() as session:
        obj = session.query(PasswordResetToken).filter(PasswordResetToken.token == token).first()
        if not obj:
            return None
        if now_ts > int(obj.expires_at):
            session.delete(obj)
            session.commit()
            return None
        return obj.email


def consume_password_reset_token(token: str) -> None:
    with get_db_session() as session:
        obj = session.query(PasswordResetToken).filter(PasswordResetToken.token == token).first()
        if obj:
            session.delete(obj)
            session.commit()


# -------------------------
# Email verify tokens
# -------------------------


def create_email_verify_token(token: str, email: str, *, expires_at: int, ip: str = "") -> None:
    with get_db_session() as session:
        obj = EmailVerifyToken(
            token=token,
            email=(email or "").lower(),
            ip=ip or "",
            expires_at=expires_at,
            created_at=_now_iso(),
        )
        session.add(obj)
        session.commit()


def consume_email_verify_token(token: str, *, now_ts: int) -> Optional[str]:
    with get_db_session() as session:
        obj = session.query(EmailVerifyToken).filter(EmailVerifyToken.token == token).first()
        if not obj:
            return None
        if now_ts > int(obj.expires_at):
            session.delete(obj)
            session.commit()
            return None
        email = obj.email
        session.delete(obj)
        session.commit()
        return email


# -------------------------
# Login audit logs
# -------------------------


def log_login_attempt(
    *,
    user_id: Optional[str],
    email: Optional[str],
    ip: str,
    user_agent: str,
    success: bool,
    reason: str = "",
) -> None:
    log_id = f"login_{int(datetime.utcnow().timestamp())}_{secrets.token_hex(8)}"
    with get_db_session() as session:
        obj = LoginAuditLog(
            id=log_id,
            user_id=user_id,
            email=(email or "").lower() if email else None,
            ip=ip or "",
            user_agent=user_agent or "",
            success=bool(success),
            reason=reason or "",
            created_at=_now_iso(),
        )
        session.add(obj)
        session.commit()


def get_last_success_login(user_id: str) -> Optional[LoginAuditLog]:
    with get_db_session() as session:
        return (
            session.query(LoginAuditLog)
            .filter(LoginAuditLog.user_id == user_id, LoginAuditLog.success == True)  # noqa: E712
            .order_by(LoginAuditLog.created_at.desc())
            .first()
        )


# -------------------------
# Password history
# -------------------------


def add_password_history(user_id: str, password_hash: str) -> None:
    hist_id = f"pwd_{int(datetime.utcnow().timestamp())}_{secrets.token_hex(8)}"
    with get_db_session() as session:
        obj = PasswordHistory(
            id=hist_id,
            user_id=user_id,
            password_hash=password_hash,
            created_at=_now_iso(),
        )
        session.add(obj)
        session.commit()


def get_recent_password_hashes(user_id: str, *, limit: int = 5) -> List[str]:
    with get_db_session() as session:
        rows = (
            session.query(PasswordHistory)
            .filter(PasswordHistory.user_id == user_id)
            .order_by(PasswordHistory.created_at.desc())
            .limit(int(limit))
            .all()
        )
        return [r.password_hash for r in rows if r.password_hash]


