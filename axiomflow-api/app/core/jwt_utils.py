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
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
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

