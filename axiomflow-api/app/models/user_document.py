from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._mixins import TimestampMixin, UuidPrimaryKeyMixin


class UserDocument(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_documents"
    __table_args__ = {"comment": "用户上传文档记录"}

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True, comment="关联用户ID"
    )
    file_name: Mapped[str] = mapped_column(
        String(255), nullable=False, default="Untitled document", server_default="Untitled document", comment="原始文件名"
    )
    file_size_bytes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0", comment="文件大小（字节）"
    )
    word_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0", comment="字数"
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="completed", server_default="completed", comment="处理状态"
    )
