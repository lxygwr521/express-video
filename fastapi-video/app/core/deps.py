"""FastAPI 依赖注入：数据库会话、当前用户认证"""

from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.security import verify_token

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    required: bool = True,
) -> Optional[dict]:
    """
    验证当前登录用户。

    参数:
        required=True  → 未登录返回 402（原 Express 约定：402 表示认证失败）
        required=False → 未登录返回 None（可选认证，如视频详情/评论列表）
    """
    token = None
    if credentials:
        token = credentials.credentials

    if not token:
        if required:
            raise HTTPException(status_code=402, detail="未提供认证 Token")
        return None

    payload = verify_token(token)
    if not payload:
        if required:
            raise HTTPException(status_code=402, detail="Token 无效或已过期")
        return None

    return payload


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[dict]:
    """可选登录 — 有 Token 就解析，没有也不报错"""
    if not credentials:
        return None
    payload = verify_token(credentials.credentials)
    return payload if payload else None

