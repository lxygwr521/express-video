"""消息路由 — 迁移自 router/message.js + messageController.js"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.services import message_service

router = APIRouter()


def _uid(user: dict) -> int:
    return user["userinfo"]["id"]

# HTTP (message.py)     → 历史数据：会话列表、消息记录
# WebSocket (websocket.py) → 实时数据：在线收发消息

# ============================================================
# GET /conversations — 会话列表
# ============================================================
@router.get("/conversations")
async def list_conversations(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversations = await message_service.get_conversations(db, _uid(user))
    return {"conversations": conversations}


# ============================================================
# GET /conversation/{userId} — 创建或获取与某用户的会话
# ============================================================
@router.get("/conversation/{userId}")
async def get_or_create_conversation(
    userId: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    my_id = _uid(user)
    if my_id == userId:
        raise HTTPException(status_code=400, detail="不能和自己聊天")

    conv_id = await message_service.get_or_create_conversation(db, my_id, userId)
    await db.commit()
    return {"conversationId": conv_id}


# ============================================================
# GET /messages/{conversationId} — 消息列表
# ============================================================
@router.get("/messages/{conversationId}")
async def list_messages(
    conversationId: int,
    pageNum: int = 1,
    pageSize: int = 30,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await message_service.get_messages(
        db, _uid(user), conversationId, pageNum, pageSize,
    )
    if result is None:
        raise HTTPException(status_code=403, detail="无权访问该会话")
    messages, total = result
    return {"messages": messages, "total": total}
