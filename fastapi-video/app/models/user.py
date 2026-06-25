"""用户表 — 对应 Prisma User model → MySQL users"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Integer, String, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.video import Video
    from app.models.subscribe import Subscribe
    from app.models.videocomment import Videocomment
    from app.models.videolike import Videolike
    from app.models.collect import Collect
    from app.models.message import Message
    from app.models.conversation import Conversation


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(255))
    image: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    channeldes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subscribeCount: Mapped[int] = mapped_column(Integer, default=0)
    createAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updateAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # --- 关系 ---
    videos: Mapped[List["Video"]] = relationship(back_populates="user")
    subscribes: Mapped[List["Subscribe"]] = relationship(foreign_keys="Subscribe.userId", back_populates="user")
    subscribedTo: Mapped[List["Subscribe"]] = relationship(foreign_keys="Subscribe.channelId", back_populates="channel")
    videocomments: Mapped[List["Videocomment"]] = relationship(back_populates="user")
    videolikes: Mapped[List["Videolike"]] = relationship(back_populates="user")
    collects: Mapped[List["Collect"]] = relationship(back_populates="user")
    sentMessages: Mapped[List["Message"]] = relationship(foreign_keys="Message.senderId", back_populates="sender")
    conversationsAs1: Mapped[List["Conversation"]] = relationship(foreign_keys="Conversation.user1Id", back_populates="user1")
    conversationsAs2: Mapped[List["Conversation"]] = relationship(foreign_keys="Conversation.user2Id", back_populates="user2")
