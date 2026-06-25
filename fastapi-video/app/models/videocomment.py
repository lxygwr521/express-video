"""视频评论表 — 对应 Prisma Videocomment model → MySQL videocomments"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.video import Video


class Videocomment(Base):
    __tablename__ = "videocomments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text)
    videoId: Mapped[int] = mapped_column(Integer, ForeignKey("videos.id"))
    userId: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    createAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updateAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # --- 关系 ---
    video: Mapped["Video"] = relationship(back_populates="videocomments")
    user: Mapped["User"] = relationship(back_populates="videocomments")
