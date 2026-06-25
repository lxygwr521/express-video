"""消息表 — 对应 Prisma Message model → MySQL messages"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.conversation import Conversation


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversationId: Mapped[int] = mapped_column(Integer, ForeignKey("conversations.id"))
    senderId: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text)
    createAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # --- 关系 ---
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(foreign_keys=[senderId], back_populates="sentMessages")
