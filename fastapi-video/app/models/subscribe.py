"""订阅表 — 对应 Prisma Subscribe model → MySQL subscribes"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Subscribe(Base):
    __tablename__ = "subscribes"
    __table_args__ = (
        UniqueConstraint("userId", "channelId"),  # @@unique([userId, channelId])
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    userId: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    channelId: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    createAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updateAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # --- 关系 ---
    # userId = 关注者（粉丝）→ @relation("Subscriber")
    user: Mapped["User"] = relationship(foreign_keys=[userId], back_populates="subscribes")
    # channelId = 被关注者（频道主）→ @relation("Channel")
    channel: Mapped["User"] = relationship(foreign_keys=[channelId], back_populates="subscribedTo")
