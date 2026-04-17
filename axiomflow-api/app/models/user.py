from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import TimestampMixin, UuidPrimaryKeyMixin


class User(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = {"comment": "用户主表：存储账号基础信息与登录状态"}

    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True, comment="用户邮箱（登录账号）"
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, unique=True, index=True, comment="用户名（展示名，唯一）"
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="头像 URL（支持第三方登录头像）"
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")

    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="邮箱是否已验证"
    )
    is_oauth_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否已通过第三方 OAuth 完成身份验证"
    )
    translated_documents: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0", comment="累计翻译文档数"
    )
    translated_words: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0", comment="累计翻译字数"
    )
    credits_balance: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0", comment="积分余额"
    )
    notify_email: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1", comment="是否接收邮件通知"
    )
    notify_browser: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0", comment="是否接收浏览器推送"
    )
    notify_marketing: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0", comment="是否接收营销通知"
    )
    preferred_target_language: Mapped[str] = mapped_column(
        String(32), nullable=False, default="zh-CN", server_default="zh-CN", comment="默认目标语言"
    )
    ui_language: Mapped[str] = mapped_column(
        String(16), nullable=False, default="zh-CN", server_default="zh-CN", comment="界面语言"
    )
    auto_save_history: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1", comment="是否自动保存翻译历史"
    )
    enable_shortcuts: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1", comment="是否启用快捷键"
    )
    upload_size_limit_mb: Mapped[int] = mapped_column(
        Integer, nullable=False, default=20, server_default="20", comment="上传大小限制(MB)"
    )
    auto_import_provider: Mapped[str] = mapped_column(
        String(32), nullable=False, default="none", server_default="none", comment="自动导入提供方"
    )
    default_output_format: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pdf", server_default="pdf", comment="默认输出格式"
    )
    data_retention_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=7, server_default="7", comment="文档云端保留天数（-1=永久）"
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最近登录时间"
    )

    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    email_verification_tokens: Mapped[List["EmailVerificationToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[List["PasswordResetToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
