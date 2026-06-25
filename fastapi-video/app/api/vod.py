"""VOD 路由 — 迁移自 vodController.js + router/vod.js"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.services import vod_service

getvod_router = APIRouter()
playinfo_router = APIRouter()
callback_router = APIRouter()


# ============================================================
# GET /getvod
# ============================================================
@getvod_router.get("/getvod")
async def get_vod_credential(title: str, fileName: str, _user: dict = Depends(get_current_user)):
    if not title or not fileName:
        raise HTTPException(status_code=400, detail="缺少 title 或 fileName 参数")
    try:
        return await vod_service.get_upload_credential(title, fileName)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "获取上传凭证失败", "detail": str(e)})


# ============================================================
# GET /playinfo/{videoId}
# ============================================================
@playinfo_router.get("/playinfo/{videoId}")
async def get_play_info(videoId: str, _user: dict | None = Depends(lambda: get_current_user(required=False))):
    if not videoId:
        raise HTTPException(status_code=400, detail="缺少视频ID")
    try:
        result = await vod_service.get_play_info(videoId)
        if not result["playInfoList"]:
            raise HTTPException(status_code=404, detail="未找到视频播放信息")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "获取播放信息失败", "detail": str(e)})


# ============================================================
# POST /callback
# ============================================================
@callback_router.post("/callback")
async def vod_callback(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="请求体格式错误")

    event_type = body.get("EventType", "")
    video_id = body.get("VideoId", "")
    status = body.get("Status", "")
    cover_url = body.get("CoverUrl", "")

    if event_type != "SnapshotComplete":
        raise HTTPException(status_code=400, detail="非截图事件")
    if not video_id:
        raise HTTPException(status_code=400, detail="缺少 VideoId")
    if status != "success" or not cover_url:
        print(f"VOD 截图回调: VideoId={video_id} 截图未成功或无封面")
        raise HTTPException(status_code=400, detail="截图未成功")

    ok = await vod_service.update_cover_by_vod_id(db, video_id, cover_url)
    if not ok:
        raise HTTPException(status_code=404, detail="视频不存在")

    await db.commit()
    print(f"VOD 截图回调: vodvideoId={video_id} 封面已更新")
    return {"msg": "封面更新成功"}
