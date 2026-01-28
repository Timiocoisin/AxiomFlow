"""
FastAPI 依赖函数
提供获取当前用户等常用依赖
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..core.jwt_utils import verify_token
from ..core.auth_db import is_session_active
from ..core.user_db import get_user_by_id, get_db_session
import os
from ..db.schema import User

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    从JWT token中获取当前登录用户
    
    Args:
        credentials: HTTP Bearer token
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: token无效或用户不存在
    """
    token = credentials.credentials
    try:
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # access token 短期撤销策略（会话级）：
        # 若该 access token 携带 sid，则检查该会话是否仍活跃。
        sid = str(payload.get("sid") or "").strip()
        if sid:
            now_ts = int(__import__("time").time())
            if not is_session_active(user_id=str(user_id), session_id=sid, now_ts=now_ts):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="会话已失效，请重新登录",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        return user
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_optional)
) -> User | None:
    """
    可选获取当前用户（如果未登录返回None）
    
    Args:
        credentials: HTTP Bearer token（可选）
        
    Returns:
        User | None: 当前用户对象或None
    """
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def require_verified_email(current_user: User = Depends(get_current_user)) -> User:
    """
    要求用户邮箱已验证（用于敏感操作）。
    默认策略：未验证允许登录，但禁止敏感操作（可通过配置关闭该限制）。
    """
    enabled_raw = os.getenv("REQUIRE_EMAIL_VERIFIED_FOR_SENSITIVE_OPS", "true").strip().lower()
    enabled = enabled_raw not in ("0", "false", "no", "off")
    if not enabled:
        return current_user

    if getattr(current_user, "email_verified", False):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="邮箱未验证：请先完成邮箱验证后再执行该操作",
    )

