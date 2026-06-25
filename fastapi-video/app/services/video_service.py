"""视频模块业务逻辑 — 迁移自 videoController.js"""

from typing import Optional
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.user import User
from app.models.video import Video
from app.models.videolike import Videolike
from app.models.collect import Collect
from app.models.videocomment import Videocomment
from app.models.subscribe import Subscribe
from app.core.redis import (
    hot_inc, top_hots, hot_remove,
    toggle_like, toggle_dislike, toggle_collect, get_user_video_status,
)
from app.core.vod_client import vod_request


# ============================================================
# 热度排行
# ============================================================
async def get_hots(n: int, db: AsyncSession) -> list[dict]:
    tops = await top_hots(n)
    if not tops:
        return []
    video_ids = [int(item["videoId"]) for item in tops]
    r = await db.execute(select(Video.id, Video.title).where(Video.id.in_(video_ids)))
    title_map = {vid: title for vid, title in r.all()}
    return [
        {"videoId": item["videoId"], "score": item["score"],
         "title": title_map.get(int(item["videoId"]), "")}
        for item in tops
    ]


# ============================================================
# 视频列表（分页）
# ============================================================
async def get_video_list(db: AsyncSession, page: int, size: int) -> tuple[list[dict], int]:
    offset = (page - 1) * size
    total_r = await db.execute(select(func.count(Video.id)))
    total = total_r.scalar()

    r = await db.execute(
        select(Video)
        .options(
            joinedload(Video.user).load_only(User.id, User.username, User.image),
            joinedload(Video.videocomments),
        )
        .order_by(Video.createAt.desc())
        .offset(offset).limit(size)
    )
    videos = r.unique().scalars().all()

    result = []
    for v in videos:
        result.append({
            "id": v.id, "title": v.title, "descrption": v.descrption,
            "vodvideoId": v.vodvideoId, "userId": v.userId,
            "cover": v.cover, "createAt": v.createAt, "updateAt": v.updateAt,
            "user": {"id": v.user.id, "username": v.user.username, "image": v.user.image} if v.user else None,
            "commentCount": len(v.videocomments),
        })
    return result, total


# ============================================================
# 视频详情
# ============================================================
async def get_video_detail(db: AsyncSession, video_id: int, current_user_id: int | None) -> dict | None:
    r = await db.execute(
        select(Video)
        .options(
            joinedload(Video.user).load_only(User.id, User.username, User.image, User.subscribeCount),
        )
        .where(Video.id == video_id)
    )
    video = r.unique().scalar()
    if not video:
        return None

    # 点赞/踩计数
    like_r = await db.execute(select(func.count(Videolike.id)).where(Videolike.videoId == video_id, Videolike.like == 1))
    dislike_r = await db.execute(select(func.count(Videolike.id)).where(Videolike.videoId == video_id, Videolike.like == -1))
    comment_r = await db.execute(select(func.count(Videocomment.id)).where(Videocomment.videoId == video_id))

    result = {
        "id": video.id, "title": video.title, "descrption": video.descrption,
        "vodvideoId": video.vodvideoId, "userId": video.userId,
        "cover": video.cover, "createAt": video.createAt, "updateAt": video.updateAt,
        "user": {"id": video.user.id, "username": video.user.username,
                 "image": video.user.image, "subscribeCount": video.user.subscribeCount} if video.user else None,
        "commentCount": comment_r.scalar(),
        "likeCount": like_r.scalar(),
        "dislikeCount": dislike_r.scalar(),
        "islike": False, "isDislike": False, "isSubscribe": False, "isCollect": False,
    }

    if current_user_id:
        channel_id = video.user.id if video.user else video.userId
        # 优先 Redis
        redis_status = await get_user_video_status(current_user_id, video_id)
        if redis_status:
            result["islike"] = redis_status["isLiked"]
            result["isDislike"] = redis_status["isDisliked"]
            result["isCollect"] = redis_status["isCollected"]
        else:
            # DB 回退
            l = await db.execute(select(Videolike).where(Videolike.userId == current_user_id, Videolike.videoId == video_id, Videolike.like == 1))
            if l.scalar(): result["islike"] = True
            d = await db.execute(select(Videolike).where(Videolike.userId == current_user_id, Videolike.videoId == video_id, Videolike.like == -1))
            if d.scalar(): result["isDislike"] = True
            c = await db.execute(select(Collect).where(Collect.userId == current_user_id, Collect.videoId == video_id))
            if c.scalar(): result["isCollect"] = True

        # 订阅状态
        s = await db.execute(select(Subscribe).where(Subscribe.userId == current_user_id, Subscribe.channelId == channel_id))
        if s.scalar(): result["isSubscribe"] = True

    # 观看热度
    await hot_inc(video_id, 1)
    return result


# ============================================================
# 点赞 / 点踩 / 收藏
# ============================================================
async def toggle_like_video(db: AsyncSession, user_id: int, video_id: int) -> dict:
    video = await db.get(Video, video_id)
    if not video: return None

    existing = await db.execute(
        select(Videolike).where(Videolike.userId == user_id, Videolike.videoId == video_id))
    doc = existing.scalar()
    islike, isDislike = None, None

    if doc:
        if doc.like == 1:
            await db.delete(doc); islike = False
        else:
            doc.like = 1; islike = True; isDislike = False
    else:
        db.add(Videolike(userId=user_id, videoId=video_id, like=1)); islike = True

    await db.flush()
    # Redis 异步同步
    await toggle_like(user_id, video_id)

    like_count = (await db.execute(select(func.count(Videolike.id)).where(Videolike.videoId == video_id, Videolike.like == 1))).scalar()
    dislike_count = (await db.execute(select(func.count(Videolike.id)).where(Videolike.videoId == video_id, Videolike.like == -1))).scalar()

    return {"id": video.id, "title": video.title, "likeCount": like_count, "dislikeCount": dislike_count, "islike": islike, "isDislike": isDislike}


async def toggle_dislike_video(db: AsyncSession, user_id: int, video_id: int) -> dict:
    video = await db.get(Video, video_id)
    if not video: return None

    existing = await db.execute(
        select(Videolike).where(Videolike.userId == user_id, Videolike.videoId == video_id))
    doc = existing.scalar()
    isDislike, islike = None, None

    if doc:
        if doc.like == -1:
            await db.delete(doc); isDislike = False
        else:
            doc.like = -1; isDislike = True; islike = False
    else:
        db.add(Videolike(userId=user_id, videoId=video_id, like=-1)); isDislike = True

    await db.flush()
    await toggle_dislike(user_id, video_id)

    like_count = (await db.execute(select(func.count(Videolike.id)).where(Videolike.videoId == video_id, Videolike.like == 1))).scalar()
    dislike_count = (await db.execute(select(func.count(Videolike.id)).where(Videolike.videoId == video_id, Videolike.like == -1))).scalar()

    return {"id": video.id, "title": video.title, "likeCount": like_count, "dislikeCount": dislike_count, "islike": islike, "isDislike": isDislike}


async def toggle_collect_video(db: AsyncSession, user_id: int, video_id: int) -> dict:
    video = await db.get(Video, video_id)
    if not video: return None

    existing = await db.execute(
        select(Collect).where(Collect.userId == user_id, Collect.videoId == video_id))
    doc = existing.scalar()
    is_collect = True

    if doc:
        await db.delete(doc); is_collect = False
    else:
        db.add(Collect(userId=user_id, videoId=video_id)); is_collect = True

    await db.flush()
    await toggle_collect(user_id, video_id)
    return {"isCollect": is_collect}


# ============================================================
# 我赞过的视频
# ============================================================
async def get_liked_videos(db: AsyncSession, user_id: int, page: int, size: int) -> tuple[list, int]:
    offset = (page - 1) * size
    total_r = await db.execute(select(func.count(Videolike.id)).where(Videolike.userId == user_id, Videolike.like == 1))
    total = total_r.scalar()

    r = await db.execute(
        select(Videolike)
        .where(Videolike.userId == user_id, Videolike.like == 1)
        .options(joinedload(Videolike.video))
        .offset(offset).limit(size)
    )
    likes = r.unique().scalars().all()
    result = [{"id": l.id, "video": {"id": l.video.id, "title": l.video.title, "vodvideoId": l.video.vodvideoId, "userId": l.video.userId}} for l in likes]
    return result, total


# ============================================================
# 评论
# ============================================================
async def get_comments(db: AsyncSession, video_id: int, page: int, size: int, current_user_id: int | None) -> tuple[list, int]:
    offset = (page - 1) * size
    total_r = await db.execute(select(func.count(Videocomment.id)).where(Videocomment.videoId == video_id))
    total = total_r.scalar()

    r = await db.execute(
        select(Videocomment)
        .where(Videocomment.videoId == video_id)
        .options(joinedload(Videocomment.user).load_only(User.id, User.username, User.image, User.subscribeCount))
        .offset(offset).limit(size)
    )
    comments = r.unique().scalars().all()

    # 登录用户的关注状态
    subscribed_ids = set()
    if current_user_id and comments:
        comment_user_ids = list({c.userId for c in comments})
        s = await db.execute(
            select(Subscribe.channelId).where(Subscribe.userId == current_user_id, Subscribe.channelId.in_(comment_user_ids)))
        subscribed_ids = {row[0] for row in s.all()}

    result = []
    for c in comments:
        result.append({
            "id": c.id, "content": c.content, "videoId": c.videoId, "userId": c.userId,
            "createAt": c.createAt, "updateAt": c.updateAt,
            "user": {
                "id": c.user.id, "username": c.user.username,
                "image": c.user.image, "subscribeCount": c.user.subscribeCount,
                "isSubscribed": c.userId in subscribed_ids,
            },
        })
    return result, total


async def create_comment(db: AsyncSession, video_id: int, user_id: int, content: str) -> dict:
    video = await db.get(Video, video_id)
    if not video: return None
    comment = Videocomment(content=content, videoId=video_id, userId=user_id)
    db.add(comment)
    await db.flush()
    await db.refresh(comment)  # 拿到自增 id 和 createAt/updateAt
    await hot_inc(video_id, 2)
    return {"id": comment.id, "content": comment.content, "videoId": comment.videoId,
            "userId": comment.userId, "createAt": comment.createAt, "updateAt": comment.updateAt}


async def delete_comment(db: AsyncSession, video_id: int, comment_id: int, user_id: int) -> str | None:
    video = await db.get(Video, video_id)
    if not video: return "视频不存在"
    comment = await db.get(Videocomment, comment_id)
    if not comment: return "评论不存在"
    if comment.userId != user_id: return "评论不可删除"
    await db.delete(comment)
    await db.flush()
    return None


# ============================================================
# 创建视频
# ============================================================
async def create_video(db: AsyncSession, data: dict, user_id: int) -> Video:
    video = Video(
        title=data["title"],
        descrption=data.get("descrption"),
        vodvideoId=data["vodvideoId"],
        userId=user_id,
        cover=data.get("cover"),
    )
    db.add(video)
    await db.flush()
    # flush 后需 refresh 加载服务器生成的时间戳
    await db.refresh(video)

    # 没有手动封面 → 提交 VOD 截图任务
    if not video.cover and video.vodvideoId:
        try:
            await vod_request("SubmitSnapshotJob", {
                "VideoId": video.vodvideoId,
                "SnapshotType": "CoverSnapshot",
                "Count": 1,
            })
        except Exception as e:
            print(f"提交截图任务失败: {e}")

    return video


# ============================================================
# 我的视频列表
# ============================================================
async def get_my_videos(db: AsyncSession, user_id: int, page: int, size: int) -> tuple[list[dict], int]:
    offset = (page - 1) * size
    total_r = await db.execute(select(func.count(Video.id)).where(Video.userId == user_id))
    total = total_r.scalar()

    r = await db.execute(
        select(Video)
        .where(Video.userId == user_id)
        .options(joinedload(Video.videocomments))
        .order_by(Video.createAt.desc())
        .offset(offset).limit(size)
    )
    videos = r.unique().scalars().all()

    result = []
    for v in videos:
        d = {"id": v.id, "title": v.title, "descrption": v.descrption,
             "vodvideoId": v.vodvideoId, "userId": v.userId, "cover": v.cover,
             "createAt": v.createAt, "updateAt": v.updateAt,
             "commentCount": len(v.videocomments)}
        result.append(d)
    return result, total


# ============================================================
# 删除视频
# ============================================================
async def delete_video(db: AsyncSession, video_id: int, user_id: int) -> str | None:
    video = await db.get(Video, video_id)
    if not video: return "视频不存在"
    if video.userId != user_id: return "无权删除此视频"

    # 删除关联数据
    await db.execute(delete(Collect).where(Collect.videoId == video_id))
    await db.execute(delete(Videolike).where(Videolike.videoId == video_id))
    await db.execute(delete(Videocomment).where(Videocomment.videoId == video_id))
    await db.delete(video)
    await db.flush()

    # Redis 热度移除
    await hot_remove(video_id)

    # VOD 删除
    if video.vodvideoId:
        try:
            await vod_request("DeleteVideo", {"VideoIds": video.vodvideoId})
        except Exception as e:
            print(f"VOD 视频删除失败: {e}")

    return None


# ============================================================
# 封面上传 → OSS
# ============================================================
async def upload_cover_oss(file) -> str:
    """上传封面图片到阿里云 OSS，返回公网 URL（不会过期）"""
    import uuid
    from app.core.oss import upload_file
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    key = f"covers/{uuid.uuid4().hex}.{ext}"
    content = await file.read()
    return await upload_file(key, content, f"image/{ext if ext != 'jpg' else 'jpeg'}")
