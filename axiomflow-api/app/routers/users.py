"""
用户账户管理路由
提供修改密码、查看登录历史、管理会话等功能
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi import Request as FastAPIRequest
from pydantic import BaseModel
import bcrypt
import time
from typing import List, Optional
from datetime import datetime

from ..core.dependencies import get_current_user, require_verified_email
from ..core.user_db import (
    get_user_by_id,
    update_user_password,
    user_to_dict,
)
from ..core.auth_db import (
    get_recent_password_hashes,
    add_password_history,
    log_login_attempt,
    get_login_audit_logs,
    get_user_refresh_tokens,
    delete_refresh_token,
    delete_user_refresh_tokens,
)
from ..db.schema import User, RefreshToken
from ..core.user_db import get_db_session

router = APIRouter(prefix="/users", tags=["users"])


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ChangePasswordResponse(BaseModel):
    message: str


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(require_verified_email),
):
    """
    修改密码
    """
    # 验证当前密码
    if not bcrypt.checkpw(
        request.current_password.encode("utf-8"),
        current_user.password_hash.encode("utf-8"),
    ):
        raise HTTPException(status_code=400, detail="当前密码错误")
    
    # 验证新密码强度
    from ..routers.auth import _validate_password_strong
    _validate_password_strong(request.new_password)
    
    # 密码历史检查：禁止复用最近 N 次密码
    from ..routers.auth import PASSWORD_HISTORY_LIMIT
    try:
        recent_hashes = get_recent_password_hashes(current_user.id, limit=PASSWORD_HISTORY_LIMIT)
        for old_hash in recent_hashes:
            if old_hash and bcrypt.checkpw(request.new_password.encode("utf-8"), old_hash.encode("utf-8")):
                raise HTTPException(
                    status_code=400,
                    detail=f"新密码不能与最近 {PASSWORD_HISTORY_LIMIT} 次使用过的密码相同",
                )
    except HTTPException:
        raise
    except Exception:  # pragma: no cover
        pass
    
    # 使用 bcrypt 哈希新密码
    password_hash = bcrypt.hashpw(
        request.new_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    
    # 更新密码
    if not update_user_password(current_user.email, password_hash):
        raise HTTPException(status_code=500, detail="更新密码失败")
    
    # 写入密码历史
    try:
        add_password_history(current_user.id, password_hash)
    except Exception:  # pragma: no cover
        pass
    
    # 删除所有refresh token（强制重新登录所有设备）
    try:
        delete_user_refresh_tokens(current_user.id)
    except Exception:  # pragma: no cover
        pass
    
    return ChangePasswordResponse(message="密码修改成功，请重新登录")


class LoginHistoryItem(BaseModel):
    id: str
    ip: str
    user_agent: str
    success: bool
    reason: str
    created_at: str
    login_method: str  # 登录方式：email, google, github
    device_type: str  # 设备类型：Desktop, Mobile, Tablet
    browser: str  # 浏览器
    os: str  # 操作系统


@router.get("/login-history", response_model=List[LoginHistoryItem])
async def get_login_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
):
    """
    获取登录历史（最近N条）
    """
    logs = get_login_audit_logs(current_user.id, limit=limit)
    return [
        LoginHistoryItem(
            id=log.id,
            ip=log.ip or "",
            user_agent=log.user_agent or "",
            success=log.success,
            reason=log.reason or "",
            created_at=log.created_at,
            # 如果 login_method 为空，尝试从 reason 推断，否则使用默认值
            login_method=_infer_login_method(log) or "email",
            device_type=getattr(log, "device_type", "") or "未知",
            browser=getattr(log, "browser", "") or "未知",
            os=getattr(log, "os", "") or "未知",
        )
        for log in logs
    ]


def _infer_login_method(log) -> str:
    """
    从登录记录推断登录方式
    优先使用 login_method 字段，如果为空则从 reason 推断
    """
    login_method = getattr(log, "login_method", None)
    if login_method and login_method.strip():
        return login_method.strip()
    
    # 如果 login_method 为空，尝试从 reason 推断
    reason = getattr(log, "reason", "") or ""
    if "github" in reason.lower() or "github_oauth" in reason.lower():
        return "github"
    elif "google" in reason.lower() or "google_oauth" in reason.lower():
        return "google"
    elif "email" in reason.lower() or reason in ("ok", "captcha_invalid_or_expired", "invalid_password", "user_not_found", "account_temporarily_locked"):
        return "email"
    
    # 默认返回 email
    return "email"


class SessionInfo(BaseModel):
    session_id: str  # 稳定会话ID（跨 refresh token 轮换不变）
    token: str  # 只返回token的前8位用于显示
    ip: str
    user_agent: str
    created_at: str
    last_used_at: Optional[str]
    is_current: bool  # 是否是当前会话


@router.get("/sessions", response_model=List[SessionInfo])
async def get_sessions(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user),
):
    """
    获取所有活跃会话（refresh tokens）
    """
    sessions = get_user_refresh_tokens(current_user.id)
    # 通过 access token 中的 sid 标识“当前会话”
    current_sid = ""
    try:
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            from ..core.jwt_utils import verify_token
            payload = verify_token(auth.split(" ", 1)[1].strip()) or {}
            current_sid = str(payload.get("sid") or "")
    except Exception:
        current_sid = ""
    
    return [
        SessionInfo(
            session_id=getattr(session, "session_id", "") or "",
            token=session.token[:8] + "..." if len(session.token) > 8 else session.token,
            ip=session.ip or "",
            user_agent=session.user_agent or "",
            created_at=session.created_at,
            last_used_at=session.last_used_at or None,
            is_current=bool(current_sid and (getattr(session, "session_id", "") or "") == current_sid),
        )
        for session in sessions
    ]


@router.delete("/sessions/{token_prefix}")
async def revoke_session(
    token_prefix: str,
    current_user: User = Depends(get_current_user),
):
    """
    撤销指定会话（优先按 session_id 精确匹配，兼容旧版 token 前缀匹配）
    """
    sessions = get_user_refresh_tokens(current_user.id)
    deleted = False
    
    for session in sessions:
        sid = getattr(session, "session_id", "") or ""
        if (sid and sid == token_prefix) or session.token.startswith(token_prefix):
            delete_refresh_token(session.token)
            deleted = True
            break
    
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {"message": "会话已撤销"}


@router.post("/sessions/revoke-all")
async def revoke_all_sessions(
    current_user: User = Depends(get_current_user),
):
    """
    撤销所有会话（登出所有设备）
    """
    delete_user_refresh_tokens(current_user.id)
    return {"message": "所有会话已撤销，请重新登录"}

