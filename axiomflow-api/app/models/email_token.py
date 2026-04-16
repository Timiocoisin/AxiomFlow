from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import TimestampMixin, UuidPrimaryKeyMixin


class EmailVerificationToken(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "email_verification_tokens"
    __table_args__ = {"comment": "邮箱验证令牌表：用于注册后邮箱激活"}

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True, comment="关联用户ID"
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True, comment="邮箱验证Token哈希"
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, comment="过期时间"
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="使用时间（为空表示未使用）"
    )

    user = relationship("User", back_populates="email_verification_tokens")

