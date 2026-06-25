"""会话表 — 对应 Prisma Conversation model → MySQL conversations"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Integer, String, DateTime, Text, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.message import Message


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("user1Id", "user2Id"),  # @@unique([user1Id, user2Id])
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user1Id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    user2Id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    lastMessage: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lastMessageAt: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    createAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updateAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # --- 关系 ---
    user1: Mapped["User"] = relationship(foreign_keys=[user1Id], back_populates="conversationsAs1")
    user2: Mapped["User"] = relationship(foreign_keys=[user2Id], back_populates="conversationsAs2")
    messages: Mapped[List["Message"]] = relationship(back_populates="conversation")
