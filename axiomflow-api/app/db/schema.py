"""
数据库 Schema 定义

使用 SQLAlchemy ORM 定义数据模型，支持 SQLite/PostgreSQL。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, Float, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, Boolean
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

# MySQL 需要指定 VARCHAR 长度，这里统一定义常用长度
ID_LEN = 64
NAME_LEN = 255
LANG_LEN = 16
STAGE_LEN = 32
STATUS_LEN = 32
MSG_LEN = 512
PATH_LEN = 512
TIME_LEN = 32


class Project(Base):
    """项目表"""
    __tablename__ = "projects"
    __table_args__ = {"comment": "项目表：存储项目的基础信息"}

    id = Column(String(ID_LEN), primary_key=True)
    name = Column(String(NAME_LEN), nullable=False)
    user_id = Column(String(ID_LEN), nullable=True, index=True)  # 关联用户ID
    created_at = Column(String(TIME_LEN), nullable=False)  # ISO 格式时间字符串

    # 关系
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    glossary_terms = relationship("GlossaryTerm", back_populates="project", cascade="all, delete-orphan")
    batches = relationship("Batch", back_populates="project", cascade="all, delete-orphan")


class Document(Base):
    """文档表（存储文档元数据和完整 JSON 数据）"""
    __tablename__ = "documents"
    __table_args__ = {"comment": "文档表：存储文档元数据与完整 JSON 内容"}

    id = Column(String(ID_LEN), primary_key=True)
    project_id = Column(String(ID_LEN), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(ID_LEN), nullable=True, index=True)  # 关联用户ID
    title = Column(String(NAME_LEN))
    num_pages = Column(Integer, default=0)
    lang_in = Column(String(LANG_LEN), default="en")
    lang_out = Column(String(LANG_LEN), default="zh")
    status = Column(String(STATUS_LEN), default="parsed")
    json_path = Column(String(PATH_LEN), default="")  # 保留字段用于兼容，但不再使用
    json_data = Column(LONGTEXT)  # 存储完整的 JSON 数据（替代文件系统存储，使用 LONGTEXT 支持最大 4GB，MySQL 不允许默认值）
    source_pdf_path = Column(String(PATH_LEN))  # 原始 PDF 路径
    created_at = Column(String(TIME_LEN), nullable=False)
    updated_at = Column(String(TIME_LEN), nullable=False)

    # 关系
    project = relationship("Project", back_populates="documents")
    jobs = relationship("Job", back_populates="document", cascade="all, delete-orphan")


class Job(Base):
    """翻译任务表"""
    __tablename__ = "jobs"
    __table_args__ = {"comment": "翻译任务表：记录文档的翻译进度与状态"}

    id = Column(String(ID_LEN), primary_key=True)
    document_id = Column(String(ID_LEN), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String(STAGE_LEN), default="pending")  # pending, translating, success, failed
    progress = Column(Float, default=0.0)  # 0.0 ~ 1.0
    message = Column(String(MSG_LEN), default="")
    created_at = Column(String(TIME_LEN), nullable=False)
    updated_at = Column(String(TIME_LEN), nullable=False)

    # 关系
    document = relationship("Document", back_populates="jobs")


class Batch(Base):
    """批次表"""
    __tablename__ = "batches"
    __table_args__ = {"comment": "批次表：批量上传/翻译任务的分组信息"}

    id = Column(String(ID_LEN), primary_key=True)
    project_id = Column(String(ID_LEN), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    document_ids = Column(JSON, nullable=False)  # list[str] - 文档 ID 列表
    job_ids = Column(JSON, default=list)  # list[str] - 任务 ID 列表（可选）
    created_at = Column(String(TIME_LEN), nullable=False)
    updated_at = Column(String(TIME_LEN), nullable=False)

    # 关系
    project = relationship("Project", back_populates="batches")


class GlossaryTerm(Base):
    """术语表"""
    __tablename__ = "glossary_terms"

    id = Column(String(ID_LEN), primary_key=True)
    project_id = Column(String(ID_LEN), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    term = Column(String(NAME_LEN), nullable=False)
    translation = Column(String(NAME_LEN), nullable=False)
    created_at = Column(String(TIME_LEN), nullable=False)
    updated_at = Column(String(TIME_LEN), nullable=False)

    # 关系
    project = relationship("Project", back_populates="glossary_terms")

    # 唯一约束：同一项目内，术语不能重复
    __table_args__ = (
        UniqueConstraint("project_id", "term", name="uq_project_term"),
        {"comment": "术语表：存储项目级术语及其翻译，支持术语一致性"},
    )


class TranslationMemory(Base):
    """翻译记忆表（参数化缓存）"""
    __tablename__ = "translation_memory"
    __table_args__ = {"comment": "翻译记忆表：按引擎与参数缓存原文与译文结果"}

    # 注意：SQLAlchemy ORM 映射必须有主键（primary key）。
    # 这里用一个独立的 id 作为主键，同时保留组合唯一约束用于"参数化缓存"去重。
    id = Column(String(ID_LEN), primary_key=True)

    translate_engine = Column(String(100), nullable=False)  # 翻译服务名称
    translate_params = Column(Text, nullable=False)  # JSON 格式的参数（已规范化）
    original_text = Column(Text, nullable=False)  # 原文（数学符号已保护）
    translated_text = Column(Text, nullable=False)  # 译文
    created_at = Column(String(TIME_LEN), nullable=False)
    updated_at = Column(String(TIME_LEN), nullable=False)

    # 注：MySQL 不允许在 TEXT 上直接建唯一索引；如需去重，可在业务侧加哈希字段后再建索引


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(String(ID_LEN), primary_key=True)
    email = Column(String(NAME_LEN), unique=True, nullable=False, index=True)
    name = Column(String(NAME_LEN), nullable=False)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash
    provider = Column(String(32), nullable=False, default="email")  # email, google, github
    avatar = Column(String(PATH_LEN), default="" )  # 头像URL
    created_at = Column(String(TIME_LEN), nullable=False)
    updated_at = Column(String(TIME_LEN), nullable=False)

    # 唯一约束：邮箱必须唯一
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
        {"comment": "用户表：存储用户账号、密码哈希、邮箱验证等基础信息"},
    )


class CaptchaSession(Base):
    """图形验证码会话（持久化）"""
    __tablename__ = "auth_captcha_sessions"
    __table_args__ = {"comment": "图形验证码会话：存储验证码哈希与过期时间，用于表单校验"}

    session_id = Column(String(ID_LEN), primary_key=True)
    code_hash = Column(String(64), nullable=False)  # sha256 hex
    ip = Column(String(64), default="")
    expires_at = Column(Integer, nullable=False)  # epoch seconds
    created_at = Column(String(TIME_LEN), nullable=False)


class EmailCodeSession(Base):
    """邮箱验证码会话（用于忘记密码验证码）"""
    __tablename__ = "auth_email_code_sessions"
    __table_args__ = {"comment": "邮箱验证码会话：存储邮箱验证码哈希与过期时间（忘记密码/登录解锁等场景）"}

    session_id = Column(String(ID_LEN), primary_key=True)
    email = Column(String(NAME_LEN), nullable=False, index=True)
    code_hash = Column(String(64), nullable=False)  # sha256 hex
    ip = Column(String(64), default="")
    expires_at = Column(Integer, nullable=False)  # epoch seconds
    created_at = Column(String(TIME_LEN), nullable=False)


class PasswordResetToken(Base):
    """密码重置 token（用于 reset-password）"""
    __tablename__ = "auth_password_reset_tokens"
    __table_args__ = {"comment": "密码重置 Token：用于三步重置密码流程中的最终重置操作"}

    token = Column(String(128), primary_key=True)
    email = Column(String(NAME_LEN), nullable=False, index=True)
    ip = Column(String(64), default="")
    expires_at = Column(Integer, nullable=False)  # epoch seconds
    created_at = Column(String(TIME_LEN), nullable=False)


class LoginAuditLog(Base):
    """登录审计日志"""
    __tablename__ = "auth_login_audit_logs"
    __table_args__ = {"comment": "登录审计日志：记录登录成功/失败、IP、UA 及原因"}

    id = Column(String(ID_LEN), primary_key=True)
    user_id = Column(String(ID_LEN), nullable=True, index=True)
    email = Column(String(NAME_LEN), nullable=True, index=True)
    ip = Column(String(64), default="", index=True)
    user_agent = Column(String(512), default="")
    success = Column(Boolean, nullable=False, default=False)
    reason = Column(String(MSG_LEN), default="")  # 失败原因/备注
    created_at = Column(String(TIME_LEN), nullable=False)


class PasswordHistory(Base):
    """密码历史（防止复用最近 N 次密码）"""
    __tablename__ = "auth_password_history"

    id = Column(String(ID_LEN), primary_key=True)
    user_id = Column(String(ID_LEN), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash
    created_at = Column(String(TIME_LEN), nullable=False)
    __table_args__ = {"comment": "密码历史：记录用户最近使用过的密码哈希，防止密码复用"}


class LoginLock(Base):
    """登录失败锁定状态（用于多进程/多实例共享锁定信息）"""
    __tablename__ = "auth_login_locks"

    id = Column(String(ID_LEN), primary_key=True)
    ip = Column(String(64), default="", index=True)
    email = Column(String(NAME_LEN), default="", index=True)
    fail_count = Column(Integer, nullable=False, default=0)
    lock_until = Column(Integer, nullable=False, default=0)  # epoch seconds，0 表示未锁定
    updated_at = Column(String(TIME_LEN), nullable=False)

    __table_args__ = (
        UniqueConstraint("ip", "email", name="uq_login_lock_ip_email"),
        {"comment": "登录锁定表：按 IP+邮箱 记录失败次数与锁定截止时间"},
    )


class RateLimitBucket(Base):
    """通用速率限制桶（用于登录/注册/忘记密码等频率控制）"""
    __tablename__ = "auth_rate_limit_buckets"

    id = Column(String(ID_LEN), primary_key=True)
    scope = Column(String(64), nullable=False, index=True)  # 例如: login, register, forgot_email, forgot_ip
    key = Column(String(NAME_LEN), nullable=False, index=True)  # 例如: ip / email
    window_seconds = Column(Integer, nullable=False)
    max_count = Column(Integer, nullable=False)
    counter = Column(Integer, nullable=False, default=0)
    window_start = Column(Integer, nullable=False)  # epoch seconds
    updated_at = Column(String(TIME_LEN), nullable=False)

    __table_args__ = (
        UniqueConstraint("scope", "key", name="uq_rate_limit_scope_key"),
        {"comment": "通用速率限制桶：按 scope+key 记录时间窗口与计数，用于接口限流"},
    )


def init_db(database_url: str) -> tuple[Any, Any]:
    """
    初始化数据库连接和会话工厂
    
    Args:
        database_url: 数据库连接 URL
            - SQLite: "sqlite:///./axiomflow.db"
            - MySQL: "mysql+pymysql://user:password@host:port/database?charset=utf8mb4"
    
    Returns:
        (engine, SessionLocal) 元组
    """
    # 对于 SQLite，启用外键约束
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    elif database_url.startswith("mysql"):
        # MySQL 特定配置
        connect_args = {
            "charset": "utf8mb4",
            "connect_timeout": 10,
        }
    
    # 设置连接池配置
    engine_kwargs = {
        "echo": False,
        "pool_pre_ping": True,  # 自动检测断开的连接并重连
        "pool_recycle": 3600,  # 1小时后回收连接
    }
    
    if database_url.startswith("mysql"):
        engine_kwargs["pool_size"] = 5
        engine_kwargs["max_overflow"] = 10
    
    engine = create_engine(database_url, connect_args=connect_args, **engine_kwargs)
    
    # 创建所有表（如果不存在）
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine, SessionLocal

