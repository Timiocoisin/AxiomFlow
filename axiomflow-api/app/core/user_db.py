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
            session.commit()  # 提交以确保对象持久化
            session.refresh(user)  # 刷新对象以确保所有属性都加载
            # 将对象从会话中分离，但保留属性值（这样对象仍然可以访问属性）
            session.expunge(user)
            return user
        except IntegrityError:
            session.rollback()
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
        user = session.query(User).filter(User.email == email.lower()).first()
        if user:
            # 将对象从会话中分离，但保留属性值
            session.expunge(user)
        return user


def get_user_by_id(user_id: str) -> Optional[User]:
    """
    根据用户ID获取用户
    
    Args:
        user_id: 用户ID
    
    Returns:
        User 对象，如果不存在则返回 None
    """
    with get_db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            # 将对象从会话中分离，但保留属性值
            session.expunge(user)
        return user


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
        session.commit()
        return True


def verify_user_email(user_id: str) -> bool:
    """
    验证用户邮箱
    
    Args:
        user_id: 用户ID
    
    Returns:
        是否验证成功
    """
    with get_db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.email_verified = True
        user.email_verified_at = datetime.utcnow().isoformat()
        user.updated_at = datetime.utcnow().isoformat()
        session.commit()
        return True


def user_to_dict(user: User) -> Dict[str, Any]:
    """
    将 User 对象转换为字典（排除敏感信息）
    
    Args:
        user: User 对象（可以是 attached 或 detached）
    
    Returns:
        用户信息字典
    """
    # 如果对象是 detached，尝试通过 ID 重新查询
    try:
        # 尝试访问属性，如果失败说明是 detached
        _ = user.id
        _ = user.email
        # 如果成功，直接使用
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "provider": user.provider,
            "avatar": user.avatar or "",
            "has_password": bool(getattr(user, "password_hash", "") or ""),
            "email_verified": getattr(user, "email_verified", False),
            "email_verified_at": getattr(user, "email_verified_at", None),
        }
    except Exception:
        # 如果是 detached，通过 ID 重新查询
        if hasattr(user, 'id') and user.id:
            with get_db_session() as session:
                fresh_user = session.query(User).filter(User.id == user.id).first()
                if fresh_user:
                    return {
                        "id": fresh_user.id,
                        "email": fresh_user.email,
                        "name": fresh_user.name,
                        "provider": fresh_user.provider,
                        "avatar": fresh_user.avatar or "",
                        "has_password": bool(getattr(fresh_user, "password_hash", "") or ""),
                        "email_verified": getattr(fresh_user, "email_verified", False),
                        "email_verified_at": getattr(fresh_user, "email_verified_at", None),
                    }
        # 如果无法获取，返回基本信息
        return {
            "id": getattr(user, 'id', ''),
            "email": getattr(user, 'email', ''),
            "name": getattr(user, 'name', ''),
            "provider": getattr(user, 'provider', 'email'),
            "avatar": getattr(user, 'avatar', '') or "",
            "has_password": bool(getattr(user, "password_hash", "") or ""),
            "email_verified": getattr(user, 'email_verified', False),
            "email_verified_at": getattr(user, 'email_verified_at', None),
        }

