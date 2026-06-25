"""SQLAlchemy async engine + session 工厂

SQLAlchemy 是 Python 最流行的 ORM（对象关系映射），作用等价于 Node.js 的 Prisma。
它会自动把 Python 类（模型）翻译成 SQL 语句，和对 MySQL 数据库交互。

核心概念：
  Engine   — 数据库连接池，全局只有一个
  Session  — 一次数据库会话（事务），每个请求创建一个
  async    — 异步 IO，不阻塞事件循环（等价于 Node.js 的 async/await）
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import settings

# ============================================================================
# Engine — 数据库连接池
# ============================================================================
# Engine 是整个应用与数据库通信的唯一入口，内部管理了一个连接池（connection pool）。
# 它很"重"，所以全局只创建一次（模块级别的单例），不会每个请求都 new。
#
# create_async_engine:
#   参数1: 数据库连接串（DSN）
#     mysql+aiomysql://user:pass@host:port/dbname
#     └─┬─┘ └──┬──┘
#     dialect  driver
#     dialect:  数据库类型（mysql / postgresql / sqlite）
#     driver:   异步驱动（aiomysql = MySQL 的 asyncio 驱动）
#
#   echo=True:    打印每条 SQL 语句（调试时开，生产关）
#   pool_size=10: 连接池常驻连接数（默认 5，高并发场景调大）
#   max_overflow: pool_size 满了之后允许临时多开的连接上限（总数 = 10 + 20 = 30）
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,            # 不打印 SQL，开发调试时可改为 True
    pool_size=10,          # 常驻 10 个连接
    max_overflow=20,       # 峰值可临时增开 20 个，总计最多 30

    # pool_recycle=3600,   # 连接最大存活秒数，超过后自动回收重连（MySQL 默认 8h 断开）
    # pool_pre_ping=True,  # 每次使用前向 MySQL 发 ping 检测连接是否存活（生产建议开启）
)

# ============================================================================
# Session 工厂 — 每次请求创建一个数据库会话
# ============================================================================
# Session 是数据库事务的载体。所有的查询（SELECT）、插入（INSERT）、更新（UPDATE）
# 都在 Session 里进行。可以把 Session 理解为一个"草稿本"：
#   - 你对模型做的修改、新增、删除，先记在这个草稿上
#   - 调用 commit() 后，草稿才真正写入数据库
#   - 调用 rollback() 则丢弃草稿，取消所有改动
#
# async_sessionmaker:
#   快速创建 Session 的工厂函数。每次调用它都会返回一个新的 AsyncSession 实例。
#
#   bind=engine:           这个工厂生产的 Session 用哪个数据库连接
#   class_=AsyncSession:   生产的 Session 类型（异步版本）
#   expire_on_commit=False: commit 后不"过期"对象属性
#     - True  (Prisma 默认): commit 后再次访问对象属性会重新查库
#     - False (FastAPI 推荐): commit 后对象属性仍然可读，省一次查询
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ============================================================================
# FastAPI 依赖注入 — 为每个请求提供独立的数据库 Session
# ============================================================================
# Session 只负责提供连接，不自动提交/回滚。
# 写操作路由显式调用 await db.commit()，读操作无需 commit。
# 路由抛异常时 session 直接关闭，未提交的改动自动丢弃（等价于 rollback）。
#
# 生命周期（一次 HTTP 请求）：
#   yield session ─── 路由函数执行 ─── close()
async def get_db() -> AsyncSession:
    """为每个请求生成一个独立的数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
