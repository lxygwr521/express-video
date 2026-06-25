"""收藏表 — 对应 Prisma Collect model → MySQL collects"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

# TYPE_CHECKING: 只在 IDE/类型检查时为 True，运行时为 False
# 作用是避免循环 import，同时让 IDE 能自动补全 User 和 Video
if TYPE_CHECKING:
    from app.models.user import User
    from app.models.video import Video


class Collect(Base):
    # __tablename__：告诉 SQLAlchemy 这个类对应 MySQL 中哪张表
    # 等价于 Prisma 的 @@map("collects")
    __tablename__ = "collects"

    # __table_args__：表的额外约束（索引、唯一约束等）
    # UniqueConstraint("userId","videoId")：同一个用户不能重复收藏同一个视频
    # 等价于 Prisma 的 @@unique([userId, videoId])
    __table_args__ = (
        UniqueConstraint("userId", "videoId"),
    )

    # ===================================================================
    # 字段定义：Mapped[类型] = mapped_column(SQL类型, 约束...)
    # ===================================================================
    # Mapped[int]         — Python 类型标注，IDE 自动补全用
    # mapped_column()     — 定义数据库列的类型和约束
    #   Integer           — MySQL INT
    #   primary_key=True  — 主键
    #   autoincrement=True— 自增（MySQL AUTO_INCREMENT）
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ForeignKey("users.id") — 外键约束，引用 users 表的 id 列
    # 等价于 Prisma 的 @relation(fields: [userId], references: [id])
    userId: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    videoId: Mapped[int] = mapped_column(Integer, ForeignKey("videos.id"))

    # DateTime                          — MySQL DATETIME 类型
    # default=func.now()         — 数据库端默认值为 NOW()
    #   等价于 Prisma 的 @default(now())
    # onupdate=func.now()               — 更新行时自动设为 NOW()
    #   等价于 Prisma 的 @updatedAt
    createAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updateAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # ===================================================================
    # relationship：定义 ORM 层级的关联关系（不是数据库字段！）
    # ===================================================================
    # relationship 不会在表中创建新列，它只是告诉 SQLAlchemy：
    # "当你访问 collect.user 时，自动用 userId 去 users 表查对应的用户"
    #
    # back_populates="collects"：
    #   双向关联的"回指"名——在 User 类里也有个 relationship(name="collects")
    #   两边通过 back_populates 互相关联，形成一个闭环
    user: Mapped["User"] = relationship(back_populates="collects")
    video: Mapped["Video"] = relationship(back_populates="collects")

    # 用法示例（在路由中）：
    #   result = await db.execute(
    #     select(Collect).where(Collect.userId == uid).options(joinedload(Collect.video))
    #   )
    #   collect = result.scalar()
    #   print(collect.video.title)  # ← relationship 让这行不需要手动 JOIN
