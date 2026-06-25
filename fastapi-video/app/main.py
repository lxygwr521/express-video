"""FastAPI 应用入口"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动 / 关闭"""
    # 启动时：初始化 Redis Lua 脚本
    from app.core.redis import init_lua_scripts, redis
    await init_lua_scripts()
    print(f"Server starting on port {settings.PORT}...")

    # 自动建表（Prisma 的 db push 等价操作）
    from app.database import engine
    import app.models  # noqa: F401 — 确保所有模型注册到 Base.metadata
    from app.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables ensured.")

    yield
    # 关闭时
    await redis.aclose()
    print("Server shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)


# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- 请求耗时日志中间件  作用于所有http请求 ----------
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000)
    print(f"[{request.method}] {request.url.path} {response.status_code} {duration}ms")
    return response


# ---------- 全局异常处理 ----------
# 只兜底意料之外的异常。HTTPException（402/404 等）由 FastAPI 内置处理器正常返回，
# 不会被这里的 500 吞掉。
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from fastapi import HTTPException as FastAPIHTTPException
    # HTTPException 不是 bug，是故意抛的（如 402 未登录、404 不存在），交给 FastAPI 自己处理
    if isinstance(exc, FastAPIHTTPException):
        raise exc
    print(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "服务器内部错误，请稍后重试"},
    )


# ---------- 测试路由 ----------
@app.get("/ping")
async def ping():
    return {"message": "pong", "timestamp": int(time.time() * 1000)}


# ---------- 挂载业务路由 ----------
from app.api import router as api_router
app.include_router(api_router, prefix="/api/v1")

# ---------- 挂载 WebSocket（Socket.IO） ----------
# python-socketio 通过 ASGIApp 包装，让 HTTP 和 WS 共用同一端口
import socketio as _socketio
from app.core.websocket import sio
app = _socketio.ASGIApp(sio, app)
