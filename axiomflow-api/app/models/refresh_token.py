from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import TimestampMixin, UuidPrimaryKeyMixin


class RefreshToken(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "refresh_tokens"
    __table_args__ = {"comment": "刷新令牌表：维护会话续期与设备登录状态"}

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True, comment="关联用户ID"
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True, comment="Refresh Token 哈希"
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, comment="过期时间"
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="吊销时间（为空表示有效）"
    )

    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="客户端UA")
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="客户端IP")

    user = relationship("User", back_populates="refresh_tokens")

