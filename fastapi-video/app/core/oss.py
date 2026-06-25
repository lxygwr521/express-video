"""阿里云 OSS 客户端 — 迁移自 model/oss.js

用于上传封面图片和头像到 OSS，返回公网 URL，不会过期。
"""

import oss2
from app.config import settings

_BUCKET = None


def _get_bucket():
    """延迟初始化 OSS Bucket（首次调用时连接）"""
    global _BUCKET
    if _BUCKET is None:
        auth = oss2.Auth(settings.ALIYUN_ACCESS_KEY_ID, settings.ALIYUN_ACCESS_KEY_SECRET)
        _BUCKET = oss2.Bucket(auth, f"https://{settings.OSS_REGION}.aliyuncs.com", settings.OSS_BUCKET)
    return _BUCKET


async def upload_file(key: str, data: bytes, content_type: str = "image/jpeg") -> str:
    """上传文件到 OSS，返回公网 HTTPS URL"""
    bucket = _get_bucket()
    bucket.put_object(key, data, headers={"Content-Type": content_type})
    return f"https://{settings.OSS_BUCKET}.{settings.OSS_REGION}.aliyuncs.com/{key}"
