from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._mixins import TimestampMixin, UuidPrimaryKeyMixin


class ApiKey(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "api_keys"
    __table_args__ = {"comment": "API 密钥表：用于第三方调用鉴权"}

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True, comment="关联用户ID"
    )
    key_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True, comment="API Key 哈希"
    )
    key_prefix: Mapped[str] = mapped_column(
        String(24), nullable=False, comment="API Key 前缀"
    )
    key_last4: Mapped[str] = mapped_column(
        String(4), nullable=False, comment="API Key 后四位"
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最近使用时间"
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="吊销时间（为空表示可用）"
    )
