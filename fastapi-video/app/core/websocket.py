"""WebSocket 实时消息 — python-socketio（迁移自 model/websocket.js）

注意：python-socketio的ASGI事件处理器没有SQLAlchemy的greenlet上下文，
     所有DB操作必须用run_sync()包装，不能用 await db.execute()。
"""

import socketio
from app.core.security import verify_token
from app.database import AsyncSessionLocal

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


# ---- JWT 鉴权 ----
@sio.event
async def connect(sid, environ, auth):
    token = (auth or {}).get("token") if isinstance(auth, dict) else None
    if not token:
        qs = environ.get("QUERY_STRING", "")
        for pair in qs.split("&"):
            if pair.startswith("token="):
                token = pair.split("=", 1)[1]
                break
    if not token:
        raise socketio.exceptions.ConnectionRefusedError("未登录")

    payload = verify_token(token)
    if not payload:
        raise socketio.exceptions.ConnectionRefusedError("token 无效")

    async with sio.session(sid) as session:
        session["user_id"] = payload["userinfo"]["id"]

    print(f"[WS] 用户 {payload['userinfo']['id']} 已连接")


# ---- 加入私聊房间 ----
@sio.event
async def join_conversation(sid, conversationId):
    sio.enter_room(sid, f"conversation:{conversationId}")


# ---- 发送消息（全部 DB 操作走 run_sync，不依赖 greenlet） ----
@sio.event
async def send_message(sid, data):
    session = await sio.get_session(sid)
    user_id = session.get("user_id")
    if not user_id:
        return {"error": "未登录"}

    conversation_id = data.get("conversationId")
    content = (data.get("content") or "").strip()
    recipient_id = data.get("recipientId")

    if not content:
        return {"error": "消息不能为空"}

    async with AsyncSessionLocal() as db:

        def _save_and_commit(sync_db):
            from datetime import datetime, timezone
            from app.models.conversation import Conversation
            from app.models.message import Message
            from app.models.user import User

            # 1. 解析/创建会话
            conv_id = conversation_id
            if not conv_id and recipient_id:
                u1, u2 = min(user_id, recipient_id), max(user_id, recipient_id)
                conv = sync_db.query(Conversation).filter(
                    Conversation.user1Id == u1,
                    Conversation.user2Id == u2,
                ).first()
                if not conv:
                    conv = Conversation(user1Id=u1, user2Id=u2)
                    sync_db.add(conv)
                    sync_db.flush()
                conv_id = conv.id

            if not conv_id:
                raise ValueError("缺少 conversationId 或 recipientId")

            # 2. 保存消息
            msg = Message(
                conversationId=conv_id,
                senderId=user_id,
                content=content,
            )
            sync_db.add(msg)
            sync_db.flush()

            # 3. 更新会话最后消息
            conv = sync_db.get(Conversation, conv_id)
            if conv:
                conv.lastMessage = content
                conv.lastMessageAt = datetime.now(timezone.utc)

            # 4. 取 sender 信息
            sender = sync_db.get(User, user_id)

            sync_db.commit()

            return {
                "id": msg.id,
                "content": msg.content,
                "senderId": msg.senderId,
                "createAt": msg.createAt.isoformat() if msg.createAt else "",
                "conversationId": conv_id,
                "sender": {
                    "id": sender.id,
                    "username": sender.username,
                    "image": sender.image,
                } if sender else None,
            }

        try:
            result = await db.run_sync(_save_and_commit)
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            import traceback
            print(f"[WS] 发送失败: {traceback.format_exc()}")
            return {"error": str(e)}

        msg = {
            "id": result["id"],
            "content": result["content"],
            "senderId": result["senderId"],
            "createAt": result["createAt"],
            "sender": result["sender"],
        }
        payload = {"conversationId": result["conversationId"], "message": msg}
        # 发给接收方（room）+ 发送者（to=sid）
        room = f"conversation:{result['conversationId']}"
        await sio.emit("new_message", payload, room=room, skip_sid=sid)
        await sio.emit("new_message", payload, to=sid)
        print(f"[WS] new_message emitted to {room} + sender {sid}")
        return {"success": True, "message": msg}


# ---- 断开连接 ----
@sio.event
async def disconnect(sid):
    try:
        session = await sio.get_session(sid)
        uid = session.get("user_id", "?")
    except Exception:
        uid = "?"
    print(f"[WS] 用户 {uid} 断开连接")
