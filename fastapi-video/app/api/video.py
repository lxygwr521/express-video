"""视频路由 — 迁移自 router/video.js + videoController.js (14接口)"""

from functools import partial
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.services import video_service
from app.api.vod import getvod_router, playinfo_router

router = APIRouter()
router.include_router(getvod_router, tags=["VOD"])
router.include_router(playinfo_router, tags=["VOD"])


def _uid(user: dict) -> int:
    return user["userinfo"]["id"]


# ============================================================
# GET /gethots/{topnum}
# ============================================================
@router.get("/gethots/{topnum}")
async def get_hots(topnum: int, db: AsyncSession = Depends(get_db)):
    return {"tops": await video_service.get_hots(topnum, db)}


# ============================================================
# POST /collect/{videoId}
# ============================================================
@router.post("/collect/{videoId}")
async def collect_video(videoId: int, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await video_service.toggle_collect_video(db, _uid(user), videoId)
    if result is None:
        raise HTTPException(status_code=404, detail="视频不存在")
    await db.commit()
    return result


# ============================================================
# POST /likelist
# ============================================================
@router.post("/likelist")
async def liked_list(body: dict = Body(...), user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    page, size = body.get("pageNum", 1), body.get("pageSize", 10)
    likes, total = await video_service.get_liked_videos(db, _uid(user), page, size)
    return {"likes": likes, "likeCount": total}


# ============================================================
# POST /dislike/{videoId}
# ============================================================
@router.post("/dislike/{videoId}")
async def dislike_video(videoId: int, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await video_service.toggle_dislike_video(db, _uid(user), videoId)
    if result is None:
        raise HTTPException(status_code=404, detail="视频不存在")
    await db.commit()
    return result


# ============================================================
# POST /like/{videoId}
# ============================================================
@router.post("/like/{videoId}")
async def like_video(videoId: int, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await video_service.toggle_like_video(db, _uid(user), videoId)
    if result is None:
        raise HTTPException(status_code=404, detail="视频不存在")
    await db.commit()
    return result


# ============================================================
# DELETE /comment/{videoId}/{commentId}
# ============================================================
@router.delete("/comment/{videoId}/{commentId}")
async def delete_comment(videoId: int, commentId: int, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    err = await video_service.delete_comment(db, videoId, commentId, _uid(user))
    if err:
        code = 403 if "不可删除" in err else 404
        raise HTTPException(status_code=code, detail=err)
    await db.commit()
    return {"msg": "删除成功"}


# ============================================================
# POST /commentlist/{videoId}
# ============================================================
@router.post("/commentlist/{videoId}")
async def comment_list(
    videoId: int, body: dict = Body(...),
    user: dict | None = Depends(partial(get_current_user, required=False)),
    db: AsyncSession = Depends(get_db),
):
    page, size = body.get("pageNum", 1), body.get("pageSize", 10)
    uid = _uid(user) if user else None
    comments, total = await video_service.get_comments(db, videoId, page, size, uid)
    return {"comments": comments, "commentCount": total}


# ============================================================
# POST /comment/{videoId}
# ============================================================
@router.post("/comment/{videoId}", status_code=201)
async def create_comment(videoId: int, body: dict = Body(...), user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await video_service.create_comment(db, videoId, _uid(user), body.get("content", ""))
    if result is None:
        raise HTTPException(status_code=404, detail="视频不存在")
    await db.commit()
    return result


# ============================================================
# POST /videolist
# ============================================================
@router.post("/videolist")
async def video_list(body: dict = Body(...), db: AsyncSession = Depends(get_db)):
    page, size = body.get("pageNum", 1), body.get("pageSize", 10)
    videos, total = await video_service.get_video_list(db, page, size)
    return {"videolist": videos, "getvideoCount": total}


# ============================================================
# GET /video/{videoId}
# ============================================================
@router.get("/video/{videoId}")
async def video_detail(
    videoId: int,
    user: dict | None = Depends(partial(get_current_user, required=False)),
    db: AsyncSession = Depends(get_db),
):
    detail = await video_service.get_video_detail(db, videoId, _uid(user) if user else None)
    if detail is None:
        raise HTTPException(status_code=404, detail="视频不存在")
    return detail


# ============================================================
# POST /createvideo
# ============================================================
@router.post("/createvideo", status_code=201)
async def create_video(body: dict = Body(...), user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not body.get("title") or not body.get("vodvideoId"):
        raise HTTPException(status_code=400, detail="缺少必要参数")
    try:
        video = await video_service.create_video(db, body, _uid(user))
        # 必须在 commit 前读完所有属性，否则 commit 后 SQLAlchemy 可能触发延迟加载
        result = {
            "id": video.id, "title": video.title, "vodvideoId": video.vodvideoId,
            "userId": video.userId, "cover": video.cover,
            "descrption": video.descrption,
            "createAt": video.createAt.isoformat() if video.createAt else None,
            "updateAt": video.updateAt.isoformat() if video.updateAt else None,
        }
        await db.commit()
        return {"dbback": result}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
# ============================================================
# POST /myvideos
# ============================================================
@router.post("/myvideos")
async def my_videos(body: dict = Body(...), user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    page, size = body.get("pageNum", 1), body.get("pageSize", 10)
    videos, total = await video_service.get_my_videos(db, _uid(user), page, size)
    return {"videos": videos, "total": total}


# ============================================================
# DELETE /{videoId}
# ============================================================
@router.delete("/{videoId}")
async def delete_video(videoId: int, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    err = await video_service.delete_video(db, videoId, _uid(user))
    if err:
        code = 403 if "无权" in err else 404
        raise HTTPException(status_code=code, detail=err)
    await db.commit()
    return {"msg": "视频已删除"}


# ============================================================
# POST /coverimg
# ============================================================
@router.post("/coverimg", status_code=201)
async def upload_cover(coverimg: UploadFile = File(...), _user: dict = Depends(get_current_user)):
    return {"filepath": await video_service.upload_cover_oss(coverimg)}
