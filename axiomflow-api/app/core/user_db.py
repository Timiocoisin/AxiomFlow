"""
用户数据库操作函数
提供用户 CRUD 操作
"""

from contextlib import contextmanager
from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..db.schema import User, init_db, Base
from ..core.config import settings


# 初始化数据库连接
_database_url = getattr(settings, "database_url", "")
if _database_url:
    _engine, _SessionLocal = init_db(_database_url)
else:
    _engine = None
    _SessionLocal = None


@contextmanager
def get_db_session():
    """
    获取数据库会话（上下文管理器）
    
    Yields:
        Session: SQLAlchemy 数据库会话
    """
    if _SessionLocal is None:
        raise RuntimeError("数据库未配置，请设置 database_url")
    
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_user(
    email: str,
    name: str,
    password_hash: str,
    provider: str = "email",
    avatar: str = ""
) -> User:
    """
    创建新用户
    
    Args:
        email: 用户邮箱
        name: 用户名称
        password_hash: 密码哈希（bcrypt）
        provider: 登录提供商（email, google, github）
        avatar: 头像URL
    
    Returns:
        创建的 User 对象
    
    Raises:
        ValueError: 如果邮箱已存在
    """
    import secrets
    
    user_id = f"user_{int(datetime.utcnow().timestamp())}_{secrets.token_hex(8)}"
    now = datetime.utcnow().isoformat()
    
    user = User(
        id=user_id,
        email=email.lower(),
        name=name,
        password_hash=password_hash,
        provider=provider,
        avatar=avatar,
        created_at=now,
        updated_at=now
    )
    
    with get_db_session() as session:
        try:
            session.add(user)
            session.flush()  # 获取 ID
            return user
        except IntegrityError:
            raise ValueError("该邮箱已被注册")


def get_user_by_email(email: str) -> Optional[User]:
    """
    根据邮箱获取用户
    
    Args:
        email: 用户邮箱
    
    Returns:
        User 对象，如果不存在则返回 None
    """
    with get_db_session() as session:
        return session.query(User).filter(User.email == email.lower()).first()


def get_user_by_id(user_id: str) -> Optional[User]:
    """
    根据用户ID获取用户
    
    Args:
        user_id: 用户ID
    
    Returns:
        User 对象，如果不存在则返回 None
    """
    with get_db_session() as session:
        return session.query(User).filter(User.id == user_id).first()


def update_user_password(email: str, new_password_hash: str) -> bool:
    """
    更新用户密码
    
    Args:
        email: 用户邮箱
        new_password_hash: 新的密码哈希
    
    Returns:
        是否更新成功
    """
    with get_db_session() as session:
        user = session.query(User).filter(User.email == email.lower()).first()
        if not user:
            return False
        
        user.password_hash = new_password_hash
        user.updated_at = datetime.utcnow().isoformat()
        return True


def user_to_dict(user: User) -> Dict[str, Any]:
    """
    将 User 对象转换为字典（排除敏感信息）
    
    Args:
        user: User 对象
    
    Returns:
        用户信息字典
    """
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "provider": user.provider,
        "avatar": user.avatar or "",
    }

