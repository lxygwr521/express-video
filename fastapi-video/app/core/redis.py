"""Redis 客户端 + Lua 脚本 + 热度排行 + 用户状态查询

迁移自 model/redis/index.js / likeLua.js / redishotsinc.js
Lua 脚本本身不变，只改 Python 的加载和调用方式。

热度规则（与原版一致）：
  观看 +1 / 点赞 +2 / 评论 +2 / 收藏 +3
"""

import redis.asyncio as aioredis
from app.config import settings

# ============================================================
# Redis 客户端 — 全局单例
# ============================================================
redis = aioredis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD or None,
    decode_responses=True,
    protocol=2,  # 兼容旧版 Redis（<6.0 不支持 RESP3 HELLO 命令）
    # password=None 时 redis-py 不发送 AUTH
)

# ============================================================
# Lua 脚本（与原 Node.js 版完全一致）
# ============================================================

_LIKE_SCRIPT = """
local likesKey = KEYS[1]
local dislikesKey = KEYS[2]
local hotKey = KEYS[3]
local videoId = ARGV[1]

local isDisliked = redis.call('SISMEMBER', dislikesKey, videoId)
local isLiked = redis.call('SISMEMBER', likesKey, videoId)

if isLiked == 1 then
  redis.call('SREM', likesKey, videoId)
  redis.call('ZINCRBY', hotKey, -2, videoId)
  return 0
elseif isDisliked == 1 then
  redis.call('SREM', dislikesKey, videoId)
  redis.call('SADD', likesKey, videoId)
  redis.call('ZINCRBY', hotKey, 2, videoId)
  return 1
else
  redis.call('SADD', likesKey, videoId)
  redis.call('ZINCRBY', hotKey, 2, videoId)
  return 1
end
"""

_DISLIKE_SCRIPT = """
local likesKey = KEYS[1]
local dislikesKey = KEYS[2]
local hotKey = KEYS[3]
local videoId = ARGV[1]

local isLiked = redis.call('SISMEMBER', likesKey, videoId)
local isDisliked = redis.call('SISMEMBER', dislikesKey, videoId)

if isDisliked == 1 then
  redis.call('SREM', dislikesKey, videoId)
  return 0
elseif isLiked == 1 then
  redis.call('SREM', likesKey, videoId)
  redis.call('SADD', dislikesKey, videoId)
  redis.call('ZINCRBY', hotKey, -2, videoId)
  return 1
else
  redis.call('SADD', dislikesKey, videoId)
  return 1
end
"""

_COLLECT_SCRIPT = """
local collectKey = KEYS[1]
local hotKey = KEYS[2]
local videoId = ARGV[1]

local isCollected = redis.call('SISMEMBER', collectKey, videoId)

if isCollected == 1 then
  redis.call('SREM', collectKey, videoId)
  redis.call('ZINCRBY', hotKey, -3, videoId)
  return 0
else
  redis.call('SADD', collectKey, videoId)
  redis.call('ZINCRBY', hotKey, 3, videoId)
  return 1
end
"""

# ============================================================
# SHA 缓存 — 用于 evalsha，重启后重载
# ============================================================
_SHAS: dict[str, str] = {}

_LUA_MAP = {
    "like": _LIKE_SCRIPT,
    "dislike": _DISLIKE_SCRIPT,
    "collect": _COLLECT_SCRIPT,
}


async def init_lua_scripts():
    """应用启动时调用：加载 Lua 脚本到 Redis，缓存 SHA"""
    try:
        for name, script in _LUA_MAP.items():
            _SHAS[name] = await redis.script_load(script)
        print("Redis Lua 脚本加载成功")
    except Exception as e:
        print(f"Redis Lua 脚本加载失败: {e}")


# ============================================================
# Lua 脚本原子执行（含 NOSCRIPT 回退）
# ============================================================

async def _evalsha_or_eval(name: str, num_keys: int, *args) -> int:
    """用 evalsha 执行，SHA 过期时自动重载并重试"""
    sha = _SHAS.get(name)
    if not sha:
        raise RuntimeError(f"Lua 脚本未加载: {name}")

    try:
        return await redis.evalsha(sha, num_keys, *args)
    except Exception as e:
        if "NOSCRIPT" in str(e):
            # SHA 过期 → 重新加载
            await init_lua_scripts()
            sha = _SHAS.get(name)
            return await redis.evalsha(sha, num_keys, *args)
        raise


async def toggle_like(user_id: int, video_id: int) -> int:
    """点赞 toggle — 返回 1=已赞, 0=取消"""
    return await _evalsha_or_eval(
        "like", 3,
        f"user:likes:{user_id}",
        f"user:dislikes:{user_id}",
        "videohots",
        video_id,
    )


async def toggle_dislike(user_id: int, video_id: int) -> int:
    """点踩 toggle — 返回 1=已踩, 0=取消"""
    return await _evalsha_or_eval(
        "dislike", 3,
        f"user:likes:{user_id}",
        f"user:dislikes:{user_id}",
        "videohots",
        video_id,
    )


async def toggle_collect(user_id: int, video_id: int) -> int:
    """收藏 toggle — 返回 1=已收藏, 0=取消"""
    return await _evalsha_or_eval(
        "collect", 2,
        f"user:collects:{user_id}",
        "videohots",
        video_id,
    )


# ============================================================
# 用户状态查询（Pipeline，O(1)）
# ============================================================

async def get_user_video_status(user_id: int, video_id: int) -> dict | None:
    """返回 {isLiked, isDisliked, isCollected}，Redis 不可用时返回 None"""
    try:
        pipe = redis.pipeline()
        pipe.sismember(f"user:likes:{user_id}", video_id)
        pipe.sismember(f"user:dislikes:{user_id}", video_id)
        pipe.sismember(f"user:collects:{user_id}", video_id)
        results = await pipe.execute()
        return {
            "isLiked": results[0] == 1,
            "isDisliked": results[1] == 1,
            "isCollected": results[2] == 1,
        }
    except Exception:
        return None


# ============================================================
# 热度排行（Sorted Set）
# ============================================================

async def hot_inc(video_id: int, inc_num: int):
    """增加视频热度"""
    await redis.zincrby("videohots", inc_num, video_id)


async def hot_remove(video_id: int):
    """从热度榜移除视频"""
    await redis.zrem("videohots", video_id)


async def top_hots(n: int) -> list[dict]:
    """返回热度 Top N（降序，含分数）"""
    items = await redis.zrevrange("videohots", 0, n - 1, withscores=True)
    return [{"videoId": video_id, "score": score} for video_id, score in items]
