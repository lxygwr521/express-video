"""视频点赞/踩表 — 对应 Prisma Videolike model → MySQL videolikes"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.video import Video


class Videolike(Base):
    __tablename__ = "videolikes"
    __table_args__ = (
        UniqueConstraint("userId", "videoId"),  # @@unique([userId, videoId])
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    userId: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    videoId: Mapped[int] = mapped_column(Integer, ForeignKey("videos.id"))
    like: Mapped[int] = mapped_column(Integer)  # 原 @db.TinyInt，1=赞 -1=踩
    createAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updateAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # --- 关系 ---
    user: Mapped["User"] = relationship(back_populates="videolikes")
    video: Mapped["Video"] = relationship(back_populates="videolikes")
