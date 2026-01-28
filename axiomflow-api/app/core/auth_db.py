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
    EmailVerificationToken,
    RefreshToken,
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
# Email verification tokens
# -------------------------


def create_email_verification_token(token: str, user_id: str, email: str, *, expires_at: int, ip: str = "") -> None:
    """创建邮箱验证token"""
    with get_db_session() as session:
        obj = EmailVerificationToken(
            token=token,
            user_id=user_id,
            email=(email or "").lower(),
            ip=ip or "",
            expires_at=expires_at,
            created_at=_now_iso(),
        )
        session.add(obj)
        session.commit()


def get_email_verification_token_info(token: str, *, now_ts: int) -> Optional[dict]:
    """
    获取邮箱验证token信息
    
    Returns:
        dict with keys: user_id, email, or None if invalid/expired
    """
    with get_db_session() as session:
        obj = session.query(EmailVerificationToken).filter(EmailVerificationToken.token == token).first()
        if not obj:
            return None
        if now_ts > int(obj.expires_at):
            session.delete(obj)
            session.commit()
            return None
        return {
            "user_id": obj.user_id,
            "email": obj.email,
        }


def consume_email_verification_token(token: str) -> None:
    """消费（删除）邮箱验证token"""
    with get_db_session() as session:
        obj = session.query(EmailVerificationToken).filter(EmailVerificationToken.token == token).first()
        if obj:
            session.delete(obj)
            session.commit()


# -------------------------
# Refresh tokens
# -------------------------


def _sha256_hex(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def _ip_coarse(ip: str) -> str:
    """
    将 IP 归一化为“粗粒度”标识（用于会话绑定）：
    - IPv4: 取 /24 前缀（前三段）
    - IPv6/其他: 原样
    """
    ip = (ip or "").strip()
    if not ip:
        return ""
    if ":" in ip:
        return ip
    parts = ip.split(".")
    if len(parts) == 4:
        return ".".join(parts[:3]) + ".0/24"
    return ip


def _new_session_id() -> str:
    # 简短可读的会话ID（不使用 token 本身，便于 UI 展示与精确撤销）
    return secrets.token_urlsafe(16).replace("-", "").replace("_", "")


def revoke_active_sessions_for_device(user_id: str, *, user_agent: str) -> Optional[str]:
    """
    同设备单会话：按 user_agent_hash 视作“设备指纹”，撤销该设备下旧的活跃会话。

    Returns:
        被撤销会话中“既有的 session_id”（用于复用），若不存在则返回 None。
    """
    ua_hash = _sha256_hex(user_agent or "")
    if not ua_hash:
        return None

    with get_db_session() as session:
        rows = (
            session.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id)
            .filter(RefreshToken.revoked_at.is_(None))
            .filter(RefreshToken.replaced_by.is_(None))
            .filter(RefreshToken.user_agent_hash == ua_hash)
            .order_by(RefreshToken.created_at.desc())
            .all()
        )
        sid: Optional[str] = None
        if rows:
            sid = getattr(rows[0], "session_id", None) or None
            now_iso = _now_iso()
            for r in rows:
                r.revoked_at = now_iso
            session.commit()
        return sid


def create_refresh_token_record(
    token: str,
    user_id: str,
    *,
    expires_at: int,
    ip: str = "",
    user_agent: str = "",
    session_id: str | None = None,
) -> str:
    """创建refresh token记录"""
    sid = (session_id or "").strip() or _new_session_id()
    with get_db_session() as session:
        obj = RefreshToken(
            token=token,
            session_id=sid,
            user_id=user_id,
            ip=ip or "",
            user_agent=user_agent or "",
            user_agent_hash=_sha256_hex(user_agent or ""),
            ip_hash=_sha256_hex(_ip_coarse(ip or "")),
            replaced_by=None,
            revoked_at=None,
            expires_at=expires_at,
            created_at=_now_iso(),
            # 会话“最后活跃时间”：登录创建即视作活跃
            last_used_at=_now_iso(),
        )
        session.add(obj)
        session.commit()
        return sid


def consume_refresh_token_for_rotation(
    token: str,
    *,
    now_ts: int,
    ip: str,
    user_agent: str,
) -> Optional[dict]:
    """
    以“轮换”方式消费 refresh token（单次可用）：
    - 绑定会话属性：UA/IP 变化过大可拒绝
    - 重放检测：已被替换的 token 再次使用 => 判定被窃取/并发刷新，吊销用户全量 tokens
    
    Returns:
        dict with keys: user_id, session_id, old_token (RefreshToken ORM), or None if invalid/expired
    """
    with get_db_session() as session:
        # 行级锁避免并发刷新导致重放检测失效（MySQL/InnoDB 支持 FOR UPDATE）
        obj = (
            session.query(RefreshToken)
            .filter(RefreshToken.token == token)
            .with_for_update()
            .first()
        )
        if not obj:
            return None
        if now_ts > int(obj.expires_at):
            # 过期：直接标记吊销
            obj.revoked_at = _now_iso()
            session.commit()
            return None

        # 已吊销或已被替换：重放/重复使用
        if getattr(obj, "revoked_at", None) or getattr(obj, "replaced_by", None):
            user_id = obj.user_id
            # 发现重放：吊销该用户全量 tokens（防止被窃取后并发刷新）
            try:
                session.query(RefreshToken).filter(RefreshToken.user_id == user_id).update(
                    {"revoked_at": _now_iso()}
                )
                session.commit()
            except Exception:
                session.rollback()
            return None

        # 会话绑定校验：对比 UA/IP hash
        expected_ua = getattr(obj, "user_agent_hash", "") or ""
        expected_ip = getattr(obj, "ip_hash", "") or ""
        got_ua = _sha256_hex(user_agent or "")
        got_ip = _sha256_hex(_ip_coarse(ip or ""))
        if expected_ua and expected_ua != got_ua:
            # 差异巨大：吊销该用户全量 tokens
            user_id = obj.user_id
            try:
                session.query(RefreshToken).filter(RefreshToken.user_id == user_id).update(
                    {"revoked_at": _now_iso()}
                )
                session.commit()
            except Exception:
                session.rollback()
            return None
        if expected_ip and expected_ip != got_ip:
            user_id = obj.user_id
            try:
                session.query(RefreshToken).filter(RefreshToken.user_id == user_id).update(
                    {"revoked_at": _now_iso()}
                )
                session.commit()
            except Exception:
                session.rollback()
            return None

        # 更新最后使用时间（本次消费）
        obj.last_used_at = _now_iso()
        session.commit()
        return {
            "user_id": obj.user_id,
            "session_id": getattr(obj, "session_id", "") or "",
        }


def rotate_refresh_token(
    old_token: str,
    new_token: str,
    *,
    now_ts: int,
    new_expires_at: int,
    ip: str,
    user_agent: str,
) -> Optional[dict]:
    """
    原子化 refresh token 轮换：
    - 锁住旧 token 行
    - 校验过期/吊销/重放/会话绑定
    - 标记旧 token replaced_by + revoked_at
    - 插入新 token（同 session_id）

    Returns:
        dict: {user_id, session_id} 或 None（无效/重放/绑定异常）
    """
    with get_db_session() as session:
        obj = (
            session.query(RefreshToken)
            .filter(RefreshToken.token == old_token)
            .with_for_update()
            .first()
        )
        if not obj:
            return None
        if now_ts > int(obj.expires_at):
            obj.revoked_at = _now_iso()
            session.commit()
            return None
        if getattr(obj, "revoked_at", None) or getattr(obj, "replaced_by", None):
            user_id = obj.user_id
            try:
                session.query(RefreshToken).filter(RefreshToken.user_id == user_id).update(
                    {"revoked_at": _now_iso()}
                )
                session.commit()
            except Exception:
                session.rollback()
            return None

        expected_ua = getattr(obj, "user_agent_hash", "") or ""
        expected_ip = getattr(obj, "ip_hash", "") or ""
        got_ua = _sha256_hex(user_agent or "")
        got_ip = _sha256_hex(_ip_coarse(ip or ""))
        if expected_ua and expected_ua != got_ua:
            user_id = obj.user_id
            try:
                session.query(RefreshToken).filter(RefreshToken.user_id == user_id).update(
                    {"revoked_at": _now_iso()}
                )
                session.commit()
            except Exception:
                session.rollback()
            return None
        if expected_ip and expected_ip != got_ip:
            user_id = obj.user_id
            try:
                session.query(RefreshToken).filter(RefreshToken.user_id == user_id).update(
                    {"revoked_at": _now_iso()}
                )
                session.commit()
            except Exception:
                session.rollback()
            return None

        # 标记旧 token 已被替换（重放检测依赖它不被删除）
        obj.replaced_by = new_token
        obj.revoked_at = _now_iso()
        obj.last_used_at = _now_iso()

        sid = getattr(obj, "session_id", "") or _new_session_id()
        new_obj = RefreshToken(
            token=new_token,
            session_id=sid,
            user_id=obj.user_id,
            ip=ip or "",
            user_agent=user_agent or "",
            user_agent_hash=_sha256_hex(user_agent or ""),
            ip_hash=_sha256_hex(_ip_coarse(ip or "")),
            replaced_by=None,
            revoked_at=None,
            expires_at=new_expires_at,
            created_at=_now_iso(),
            # 会话“最后活跃时间”：refresh 成功即更新
            last_used_at=_now_iso(),
        )
        session.add(new_obj)
        session.commit()
        return {"user_id": obj.user_id, "session_id": sid}


def is_session_active(*, user_id: str, session_id: str, now_ts: int) -> bool:
    """
    access token 短期撤销策略（会话级）：
    - access token 内含 sid
    - 每次请求校验该 sid 是否仍有未吊销的 refresh token 记录
      => 远程登出/撤销会话后，access token 可“立刻”失效
    """
    uid = (user_id or "").strip()
    sid = (session_id or "").strip()
    if not uid or not sid:
        return True
    with get_db_session() as session:
        row = (
            session.query(RefreshToken)
            .filter(RefreshToken.user_id == uid)
            .filter(RefreshToken.session_id == sid)
            .filter(RefreshToken.revoked_at.is_(None))
            .filter(RefreshToken.replaced_by.is_(None))
            .filter(RefreshToken.expires_at > int(now_ts))
            .first()
        )
        return bool(row)


def delete_refresh_token(token: str) -> None:
    """删除refresh token"""
    with get_db_session() as session:
        obj = session.query(RefreshToken).filter(RefreshToken.token == token).first()
        if obj:
            obj.revoked_at = _now_iso()
            session.commit()


def delete_user_refresh_tokens(user_id: str) -> None:
    """删除用户的所有refresh token（用于登出所有设备）"""
    with get_db_session() as session:
        session.query(RefreshToken).filter(RefreshToken.user_id == user_id).update(
            {"revoked_at": _now_iso()}
        )
        session.commit()


# -------------------------
# User-Agent parsing
# -------------------------


def parse_user_agent(user_agent: str) -> dict[str, str]:
    """
    解析 User-Agent 字符串，提取浏览器、操作系统、设备类型
    返回: {"browser": str, "os": str, "device_type": str}
    """
    if not user_agent:
        return {"browser": "未知", "os": "未知", "device_type": "未知"}
    
    ua_lower = user_agent.lower()
    
    # 检测设备类型
    device_type = "Desktop"
    if "mobile" in ua_lower or "android" in ua_lower:
        device_type = "Mobile"
    elif "tablet" in ua_lower or "ipad" in ua_lower:
        device_type = "Tablet"
    
    # 检测浏览器
    browser = "未知"
    if "chrome" in ua_lower and "edg" not in ua_lower:
        browser = "Chrome"
    elif "firefox" in ua_lower:
        browser = "Firefox"
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        browser = "Safari"
    elif "edg" in ua_lower or "edge" in ua_lower:
        browser = "Edge"
    elif "opera" in ua_lower or "opr" in ua_lower:
        browser = "Opera"
    elif "msie" in ua_lower or "trident" in ua_lower:
        browser = "Internet Explorer"
    
    # 检测操作系统
    os_name = "未知"
    if "windows" in ua_lower:
        if "windows nt 10.0" in ua_lower or "windows nt 11" in ua_lower:
            os_name = "Windows 10/11"
        elif "windows nt 6.3" in ua_lower:
            os_name = "Windows 8.1"
        elif "windows nt 6.2" in ua_lower:
            os_name = "Windows 8"
        elif "windows nt 6.1" in ua_lower:
            os_name = "Windows 7"
        else:
            os_name = "Windows"
    elif "mac os x" in ua_lower or "macintosh" in ua_lower:
        os_name = "macOS"
    elif "linux" in ua_lower:
        os_name = "Linux"
    elif "android" in ua_lower:
        os_name = "Android"
    elif "iphone" in ua_lower or "ipod" in ua_lower:
        os_name = "iOS"
    elif "ipad" in ua_lower:
        os_name = "iPadOS"
    
    return {
        "browser": browser,
        "os": os_name,
        "device_type": device_type,
    }


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
    session_id: str = "",
    refresh_token: str = "",
    reason_code: str = "",
    reason: str = "",
    login_method: str = "email",  # email, google, github
) -> None:
    """
    记录登录尝试
    
    Args:
        user_id: 用户ID（成功时）
        email: 邮箱地址
        ip: IP地址
        user_agent: User-Agent字符串
        success: 是否成功
        reason: 原因/备注
        login_method: 登录方式（email, google, github）
    """
    log_id = f"login_{int(datetime.utcnow().timestamp())}_{secrets.token_hex(8)}"
    
    # 解析 User-Agent
    ua_info = parse_user_agent(user_agent)
    
    # 仅存 refresh token 的 hash / prefix，避免泄露明文
    rt = refresh_token or ""
    rt_hash = _sha256_hex(rt) if rt else ""
    rt_prefix = rt[:16] if rt else ""

    # 失败原因枚举化：优先使用 reason_code；兼容历史调用（reason 里传了 code）
    code = (reason_code or reason or "").strip()

    with get_db_session() as session:
        obj = LoginAuditLog(
            id=log_id,
            session_id=session_id or "",
            refresh_token_hash=rt_hash,
            refresh_token_prefix=rt_prefix,
            user_id=user_id,
            email=(email or "").lower() if email else None,
            ip=ip or "",
            user_agent=user_agent or "",
            success=bool(success),
            reason_code=code,
            reason=reason or "",
            created_at=_now_iso(),
            login_method=login_method or "email",
            device_type=ua_info.get("device_type", ""),
            browser=ua_info.get("browser", ""),
            os=ua_info.get("os", ""),
        )
        session.add(obj)
        session.commit()


def get_last_success_login(user_id: str) -> Optional[LoginAuditLog]:
    with get_db_session() as session:
        result = (
            session.query(LoginAuditLog)
            .filter(LoginAuditLog.user_id == user_id, LoginAuditLog.success == True)  # noqa: E712
            .order_by(LoginAuditLog.created_at.desc())
            .first()
        )
        if result:
            session.expunge(result)
        return result


def get_login_audit_logs(user_id: str, *, limit: int = 20) -> List[LoginAuditLog]:
    """获取用户的登录审计日志（最近N条）"""
    with get_db_session() as session:
        logs = (
            session.query(LoginAuditLog)
            .filter(LoginAuditLog.user_id == user_id)
            .order_by(LoginAuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
        # 将对象从会话中分离
        for log in logs:
            session.expunge(log)
        return logs


def has_previous_login_from_ip(user_id: str, ip: str) -> bool:
    """检查用户是否曾经从这个IP登录过（成功登录）"""
    with get_db_session() as session:
        count = (
            session.query(LoginAuditLog)
            .filter(
                LoginAuditLog.user_id == user_id,
                LoginAuditLog.ip == ip,
                LoginAuditLog.success == True  # noqa: E712
            )
            .count()
        )
        return count > 0


def get_user_refresh_tokens(user_id: str) -> List[RefreshToken]:
    """获取用户的所有refresh token"""
    with get_db_session() as session:
        tokens = (
            session.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id)
            .filter(RefreshToken.revoked_at.is_(None))
            .filter(RefreshToken.replaced_by.is_(None))
            .order_by(RefreshToken.created_at.desc())
            .all()
        )
        # 将对象从会话中分离
        for token in tokens:
            session.expunge(token)
        return tokens


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


