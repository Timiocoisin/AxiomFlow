"""
FastAPI 依赖函数
提供获取当前用户等常用依赖
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..core.jwt_utils import verify_token
from ..core.user_db import get_user_by_id, get_db_session
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

