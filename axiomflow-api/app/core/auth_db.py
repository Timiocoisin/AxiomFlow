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
    LoginAuditLog,
    PasswordHistory,
    LoginLock,
    RateLimitBucket,
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


# -------------------------
# Login lock (fail count + temporary lock)
# -------------------------


def get_login_lock(ip: str, email: str) -> Optional[dict]:
    """
    获取当前 IP + 邮箱 的锁定状态
    
    Returns:
        dict with keys: lock_until (int), fail_count (int), or None
    """
    ip_val = (ip or "").strip()
    email_val = (email or "").lower().strip()
    with get_db_session() as session:
        lock_obj = (
            session.query(LoginLock)
            .filter(LoginLock.ip == ip_val, LoginLock.email == email_val)
            .first()
        )
        if lock_obj:
            # 在会话关闭前提取所有需要的属性值，返回字典避免 DetachedInstanceError
            return {
                "lock_until": int(lock_obj.lock_until) if lock_obj.lock_until else 0,
                "fail_count": int(lock_obj.fail_count) if lock_obj.fail_count else 0,
            }
        return None


def set_login_lock(ip: str, email: str, *, fail_count: int, lock_until: int) -> None:
    """更新或创建登录锁定记录"""
    ip_val = (ip or "").strip()
    email_val = (email or "").lower().strip()
    now_iso = _now_iso()
    lock_id = f"lock_{int(datetime.utcnow().timestamp())}_{secrets.token_hex(6)}"

    with get_db_session() as session:
        obj = (
            session.query(LoginLock)
            .filter(LoginLock.ip == ip_val, LoginLock.email == email_val)
            .first()
        )
        if not obj:
            obj = LoginLock(
                id=lock_id,
                ip=ip_val,
                email=email_val,
                fail_count=int(fail_count),
                lock_until=int(lock_until),
                updated_at=now_iso,
            )
            session.add(obj)
        else:
            obj.fail_count = int(fail_count)
            obj.lock_until = int(lock_until)
            obj.updated_at = now_iso
        session.commit()


def clear_login_lock(ip: str, email: str) -> None:
    """清除登录失败计数与锁定状态"""
    ip_val = (ip or "").strip()
    email_val = (email or "").lower().strip()
    with get_db_session() as session:
        obj = (
            session.query(LoginLock)
            .filter(LoginLock.ip == ip_val, LoginLock.email == email_val)
            .first()
        )
        if obj:
            session.delete(obj)
            session.commit()


def increase_login_fail_and_maybe_lock(
    *,
    ip: str,
    email: str,
    max_failed_attempts: int,
    lock_seconds: int,
    now_ts: int,
) -> Tuple[int, Optional[int]]:
    """
    登录失败一次，增加计数，如达到上限则设置锁定。

    Returns:
        (fail_count, lock_until_ts or None)
    """
    ip_val = (ip or "").strip()
    email_val = (email or "").lower().strip()

    with get_db_session() as session:
        obj = (
            session.query(LoginLock)
            .filter(LoginLock.ip == ip_val, LoginLock.email == email_val)
            .first()
        )
        if not obj:
            obj = LoginLock(
                id=f"lock_{int(datetime.utcnow().timestamp())}_{secrets.token_hex(6)}",
                ip=ip_val,
                email=email_val,
                fail_count=0,
                lock_until=0,
                updated_at=_now_iso(),
            )
            session.add(obj)

        # 清理已过期锁定
        if obj.lock_until and now_ts > int(obj.lock_until):
            obj.fail_count = 0
            obj.lock_until = 0

        obj.fail_count = int(obj.fail_count or 0) + 1

        lock_until_ts: Optional[int] = None
        if obj.fail_count >= max_failed_attempts:
            obj.lock_until = int(now_ts + lock_seconds)
            lock_until_ts = obj.lock_until

        obj.updated_at = _now_iso()
        session.commit()

        return int(obj.fail_count), lock_until_ts


# -------------------------
# Generic rate limit bucket
# -------------------------


def check_and_increase_rate_limit(
    *,
    scope: str,
    key: str,
    limit: int,
    window_seconds: int,
    now_ts: int,
) -> bool:
    """
    通用滑动窗口/计数桶速率限制，使用数据库持久化。

    如果超限，返回 False；否则增加计数并返回 True。
    """
    scope_val = (scope or "").strip()
    key_val = (key or "").strip()
    if not scope_val or not key_val:
        return True

    with get_db_session() as session:
        obj = (
            session.query(RateLimitBucket)
            .filter(RateLimitBucket.scope == scope_val, RateLimitBucket.key == key_val)
            .first()
        )

        window_start = now_ts
        counter = 0
        if obj:
            # 检查是否仍在同一窗口
            elapsed = now_ts - int(obj.window_start)
            if elapsed < int(obj.window_seconds):
                window_start = int(obj.window_start)
                counter = int(obj.counter)
            else:
                # 新窗口，重置计数
                window_start = now_ts
                counter = 0
        else:
            obj = RateLimitBucket(
                id=f"bucket_{int(datetime.utcnow().timestamp())}_{secrets.token_hex(6)}",
                scope=scope_val,
                key=key_val,
                window_seconds=int(window_seconds),
                max_count=int(limit),
                counter=0,
                window_start=now_ts,
                updated_at=_now_iso(),
            )
            session.add(obj)

        if counter >= int(obj.max_count):
            return False

        counter += 1
        obj.counter = counter
        obj.window_start = window_start
        obj.updated_at = _now_iso()
        session.commit()

        return True


