"""
JWT 工具函数
用于生成和验证 JWT token
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from .config import settings


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT access token
    
    Args:
        data: 要编码到 token 中的数据（通常是用户ID和邮箱）
        expires_delta: token 过期时间，如果为 None 则使用默认配置
    
    Returns:
        JWT token 字符串
    """
    import secrets
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    # 给 access token 增加 jti：便于后续做黑名单/撤销策略（以及审计对齐）
    # 若调用方已显式传入 jti，则尊重调用方
    if "jti" not in to_encode:
        to_encode["jti"] = secrets.token_urlsafe(16)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证 JWT token
    
    Args:
        token: JWT token 字符串
    
    Returns:
        解码后的 payload，如果验证失败则返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def create_refresh_token(user_id: str) -> str:
    """
    创建 refresh token（不存储在JWT中，而是存储在数据库中）
    
    Args:
        user_id: 用户ID
    
    Returns:
        refresh token 字符串（随机生成，不包含JWT）
    """
    import secrets
    return secrets.token_urlsafe(64)

