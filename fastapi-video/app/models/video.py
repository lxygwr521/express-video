"""视频表 — 对应 Prisma Video model → MySQL videos"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.videocomment import Videocomment
    from app.models.videolike import Videolike
    from app.models.collect import Collect


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100))
    descrption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vodvideoId: Mapped[str] = mapped_column(String(255))
    userId: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    cover: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    createAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updateAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # --- 关系 ---
    user: Mapped["User"] = relationship(back_populates="videos")
    videocomments: Mapped[List["Videocomment"]] = relationship(back_populates="video")
    videolikes: Mapped[List["Videolike"]] = relationship(back_populates="video")
    collects: Mapped[List["Collect"]] = relationship(back_populates="video")
