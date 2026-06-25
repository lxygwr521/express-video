"""VOD 业务逻辑 — 迁移自 vodController.js"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.video import Video
from app.core.vod_client import vod_request


async def get_upload_credential(title: str, file_name: str) -> dict:
    """
    获取视频上传凭证和地址。
    返回: { VideoId, UploadAddress, UploadAuth, RequestId }
    """
    return await vod_request("CreateUploadVideo", {
        "Title": title,
        "FileName": file_name,
    })


async def get_play_info(vod_video_id: str) -> dict:
    """
    获取视频播放流地址，按清晰度排序。
    清晰度优先级: OD(原画) > HD(超清) > SD(高清) > LD(标清) > FD(流畅)
    """
    result = await vod_request("GetPlayInfo", {"VideoId": vod_video_id})

    play_info_list = result.get("PlayInfoList", {}).get("PlayInfo", [])
    if not play_info_list:
        return {"videoBase": {}, "playInfoList": [], "defaultPlayURL": "", "defaultFormat": "", "defaultDefinition": ""}

    def_order = {"OD": 5, "HD": 4, "SD": 3, "LD": 2, "FD": 1}
    sorted_list = sorted(play_info_list, key=lambda x: def_order.get(x.get("Definition", ""), 0), reverse=True)

    return {
        "videoBase": result.get("VideoBase", {}),
        "playInfoList": sorted_list,
        "defaultPlayURL": sorted_list[0].get("PlayURL", ""),
        "defaultFormat": sorted_list[0].get("Format", ""),
        "defaultDefinition": sorted_list[0].get("Definition", ""),
    }


async def submit_snapshot_job(vod_video_id: str) -> dict:
    """提交封面截图任务"""
    return await vod_request("SubmitSnapshotJob", {
        "VideoId": vod_video_id,
        "SnapshotType": "CoverSnapshot",
        "Count": 1,
    })


async def update_cover_by_vod_id(db: AsyncSession, vod_video_id: str, cover_url: str) -> bool:
    """根据 VOD VideoId 更新数据库中的封面 URL。返回是否找到视频。"""
    r = await db.execute(select(Video).where(Video.vodvideoId == vod_video_id))
    video = r.scalar()
    if not video:
        return False
    video.cover = cover_url
    await db.flush()
    return True
