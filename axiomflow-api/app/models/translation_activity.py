from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._mixins import TimestampMixin, UuidPrimaryKeyMixin


class TranslationActivity(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "translation_activities"
    __table_args__ = {"comment": "翻译活动表：记录用户翻译行为用于统计"}

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True, comment="关联用户ID"
    )
    document_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1", comment="本次翻译文档数"
    )
    word_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0", comment="本次翻译字数"
    )
    title: Mapped[str] = mapped_column(
        String(255), nullable=False, default="翻译文档", server_default="翻译文档", comment="活动标题"
    )
