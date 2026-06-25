"""消息模块业务逻辑 — 迁移自 messageController.js"""

from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.conversation import Conversation
from app.models.message import Message


async def get_conversations(db: AsyncSession, user_id: int) -> list[dict]:
    """获取当前用户的会话列表（含对方用户信息 + 最后一条消息内容）"""
    result = await db.execute(
        select(Conversation)
        .where((Conversation.user1Id == user_id) | (Conversation.user2Id == user_id))
        .order_by(Conversation.lastMessageAt.desc())
        .options(
            joinedload(Conversation.user1),
            joinedload(Conversation.user2),
        )
    )
    conversations = result.unique().scalars().all()

    # 获取每个会话的最后一条消息
    conv_ids = [c.id for c in conversations]
    last_msgs = {}
    if conv_ids:
        for cid in conv_ids:
            r = await db.execute(
                select(Message)
                .where(Message.conversationId == cid)
                .order_by(Message.createAt.desc())
                .limit(1)
            )
            last_msgs[cid] = r.scalar()

    return [
        {
            "id": c.id,
            "otherUser": {
                "id": c.user2.id if c.user1Id == user_id else c.user1.id,
                "username": c.user2.username if c.user1Id == user_id else c.user1.username,
                "image": c.user2.image if c.user1Id == user_id else c.user1.image,
            },
            "lastMessage": c.lastMessage,
            "lastMessageAt": c.lastMessageAt.isoformat() if c.lastMessageAt else None,
        }
        for c in conversations
    ]


async def get_messages(
    db: AsyncSession, user_id: int, conversation_id: int,
    page_num: int = 1, page_size: int = 30,
) -> tuple[list, int] | None:
    """获取会话的消息列表（分页）— 验证用户属于该会话"""
    conv = await db.get(Conversation, conversation_id)
    if not conv or (conv.user1Id != user_id and conv.user2Id != user_id):
        return None

    skip = (page_num - 1) * page_size
    total_r = await db.execute(
        select(func.count(Message.id)).where(Message.conversationId == conversation_id)
    )
    total = total_r.scalar()

    r = await db.execute(
        select(Message)
        .where(Message.conversationId == conversation_id)
        .order_by(Message.createAt.desc())
        .offset(skip).limit(page_size)
        .options(joinedload(Message.sender))
    )
    messages = r.unique().scalars().all()

    # 前端显示按时间正序
    msg_list = [{
        "id": m.id, "content": m.content, "senderId": m.senderId,
        "createAt": m.createAt.isoformat() if m.createAt else "",
        "sender": {"id": m.sender.id, "username": m.sender.username, "image": m.sender.image},
    } for m in reversed(messages)]

    return msg_list, total


async def get_or_create_conversation(db: AsyncSession, user_id: int, target_id: int) -> int:
    """查找或创建与 target_id 的一对一会话，返回 conversationId"""
    u1, u2 = min(user_id, target_id), max(user_id, target_id)
    r = await db.execute(
        select(Conversation).where(
            Conversation.user1Id == u1, Conversation.user2Id == u2
        )
    )
    conv = r.scalar()
    if not conv:
        conv = Conversation(user1Id=u1, user2Id=u2)
        db.add(conv)
        await db.flush()
    return conv.id


async def send_message(
    db: AsyncSession, sender_id: int,
    conversation_id: int | None, content: str,
    recipient_id: int | None = None,
) -> dict | None:
    """发送消息。无 conversation_id 时自动创建会话。返回消息字典或错误"""
    if not content or not content.strip():
        return {"error": "消息不能为空"}

    conv_id = conversation_id
    if not conv_id and recipient_id:
        conv_id = await get_or_create_conversation(db, sender_id, recipient_id)
    if not conv_id:
        return {"error": "缺少 conversationId 或 recipientId"}

    msg = Message(
        conversationId=conv_id,
        senderId=sender_id,
        content=content.strip(),
    )
    db.add(msg)
    await db.flush()

    # 更新会话最后消息
    conv = await db.get(Conversation, conv_id)
    if conv:
        conv.lastMessage = content.strip()
        conv.lastMessageAt = datetime.now(timezone.utc)

    # 返回值不需要 sender 关系数据，flush 后 id/content 已可用
    return {
        "id": msg.id, "content": msg.content,
        "senderId": msg.senderId,
        "createAt": msg.createAt.isoformat() if msg.createAt else "",
        "conversationId": conv_id,
    }
