"""API 路由聚合 — 挂载所有子路由到 /api/v1"""

from fastapi import APIRouter

router = APIRouter()

from app.api.user import router as user_router
router.include_router(user_router, prefix="/user", tags=["用户"])

from app.api.video import router as video_router
router.include_router(video_router, prefix="/video", tags=["视频"])

from app.api.vod import callback_router
router.include_router(callback_router, prefix="/vod", tags=["VOD"])

from app.api.message import router as message_router
router.include_router(message_router, prefix="/message", tags=["消息"])
