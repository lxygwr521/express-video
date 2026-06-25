"""用户模块业务逻辑 — 迁移自 userController.js"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.user import User
from app.models.subscribe import Subscribe
from app.core.security import hash_password, verify_password, create_token


# ============================================================
# 我关注的频道列表
# ============================================================
async def get_my_subscriptions(db: AsyncSession, user_id: int) -> list[dict]:
    """返回当前用户关注的所有频道（用户信息）"""
    result = await db.execute(
        select(Subscribe)
        .where(Subscribe.userId == user_id)
        .options(joinedload(Subscribe.channel))  # 等价于 Prisma include: { channel: true }
    )
    subscriptions = result.unique().scalars().all()
    return [
        {
            "id": s.channel.id,
            "username": s.channel.username,
            "image": s.channel.image,
            "subscribeCount": s.channel.subscribeCount,
            "channeldes": s.channel.channeldes,
        }
        for s in subscriptions
    ]


# ============================================================
# 某用户的粉丝列表（谁关注了他）
# ============================================================
async def get_user_fans(db: AsyncSession, channel_id: int) -> list[dict]:
    """返回关注了 channel_id 的所有用户（粉丝）"""
    result = await db.execute(
        select(Subscribe)
        .where(Subscribe.channelId == channel_id)
        .options(joinedload(Subscribe.user))
    )
    subscriptions = result.unique().scalars().all()
    return [
        {
            "id": s.user.id,
            "username": s.user.username,
            "image": s.user.image,
            "subscribeCount": s.user.subscribeCount,
            "channeldes": s.user.channeldes,
        }
        for s in subscriptions
    ]


# ============================================================
# 用户详情（含当前登录者是否关注了该用户）
# ============================================================
async def get_user_profile(
    db: AsyncSession, user_id: int, current_user_id: Optional[int]
) -> dict:
    """返回用户公开信息 + isSubscribe 状态"""
    is_subscribe = False

    if current_user_id:
        result = await db.execute(
            select(Subscribe).where(
                Subscribe.channelId == user_id,
                Subscribe.userId == current_user_id,
            )
        )
        if result.scalar():
            is_subscribe = True

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar()
    if not user:
        return None

    return {
        "id": user.id,
        "username": user.username,
        "image": user.image,
        "subscribeCount": user.subscribeCount,
        "channeldes": user.channeldes,
        "isSubscribe": is_subscribe,
    }


# ============================================================
# 取消关注
# ============================================================
async def unsubscribe(db: AsyncSession, user_id: int, channel_id: int) -> tuple[bool, Optional[str]]:
    """取消关注。返回 (成功?, 错误信息)"""
    if user_id == channel_id:
        return False, "不能取消关注自己"

    result = await db.execute(
        select(Subscribe).where(
            Subscribe.userId == user_id,
            Subscribe.channelId == channel_id,
        )
    )
    record = result.scalar()

    if not record:
        return False, "没有订阅了此频道"

    # 事务：删除订阅记录 + 减少频道主的订阅数
    await db.delete(record)
    channel = await db.get(User, channel_id)
    if channel and channel.subscribeCount > 0:
        channel.subscribeCount -= 1
    await db.flush()  # 提交由 get_db 依赖处理

    return True, None


# ============================================================
# 关注频道
# ============================================================
async def subscribe(db: AsyncSession, user_id: int, channel_id: int) -> tuple[bool, Optional[str]]:
    """关注频道。返回 (成功?, 错误信息)"""
    if user_id == channel_id:
        return False, "不能关注自己"

    result = await db.execute(
        select(Subscribe).where(
            Subscribe.userId == user_id,
            Subscribe.channelId == channel_id,
        )
    )
    record = result.scalar()

    if record:
        return False, "已经订阅了此频道"

    # 事务：创建订阅记录 + 增加频道主的订阅数
    db.add(Subscribe(userId=user_id, channelId=channel_id))
    channel = await db.get(User, channel_id)
    if channel:
        channel.subscribeCount += 1
    await db.flush()

    return True, None



async def check_email_exists(db: AsyncSession, email: str, exclude_id: int | None = None) -> bool:
    """邮箱是否已被占用（可排除自己，用于更新时）"""
    stmt = select(User).where(User.email == email)
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    r = await db.execute(stmt)
    return r.scalar() is not None


async def check_phone_exists(db: AsyncSession, phone: str, exclude_id: int | None = None) -> bool:
    """手机号是否已被占用"""
    stmt = select(User).where(User.phone == phone)
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    r = await db.execute(stmt)
    return r.scalar() is not None


async def check_username_exists(db: AsyncSession, username: str, exclude_id: int | None = None) -> bool:
    """用户名是否已被占用"""
    stmt = select(User).where(User.username == username)
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    r = await db.execute(stmt)
    return r.scalar() is not None


# ============================================================
# 用户注册
# ============================================================
async def register(db: AsyncSession, data: dict) -> User:
    """创建新用户，返回 ORM 对象"""
    user = User(
        username=data["username"],
        email=data["email"],
        password=hash_password(data["password"]),
        phone=data["phone"],
    )
    db.add(user)
    await db.flush()
    return user


# ============================================================
# 用户登录
# ============================================================
async def login(db: AsyncSession, email: str, password: str) -> Optional[dict]:
    """验证邮箱密码，返回用户信息 + JWT"""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar()

    if not user or not verify_password(password, user.password):
        return None

    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "image": user.image,
        "phone": user.phone,
        "subscribeCount": user.subscribeCount,
        "channeldes": user.channeldes,
        "createAt": user.createAt.isoformat() if user.createAt else None,
        "updateAt": user.updateAt.isoformat() if user.updateAt else None,
    }
    token = create_token(user_data)
    user_data["token"] = token
    return user_data


# ============================================================
# 更新个人信息
# ============================================================
async def update_user(db: AsyncSession, user_id: int, data: dict) -> User:
    """更新用户信息，如含密码则重新哈希"""
    user = await db.get(User, user_id)

    update_data = {k: v for k, v in data.items() if v is not None}
    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])

    for key, value in update_data.items():
        setattr(user, key, value)

    await db.flush()
    await db.refresh(user)
    return user


# ============================================================
# 头像上传
# ============================================================
async def upload_avatar(file) -> str:
    """上传头像到阿里云 OSS，返回公网 URL（不会过期）"""
    import uuid
    from app.core.oss import upload_file
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    key = f"avatars/{uuid.uuid4().hex}.{ext}"
    content = await file.read()
    return await upload_file(key, content, f"image/{ext if ext != 'jpg' else 'jpeg'}")
