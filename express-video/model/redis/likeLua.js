const { redis } = require('./index')

// Lua 脚本：点赞 toggle（原子操作）
// KEYS[1]: user:likes:{userId}       — 用户点赞集合
// KEYS[2]: user:dislikes:{userId}    — 用户点踩集合
// KEYS[3]: videohots                 — 热度排行 sorted set
// ARGV[1]: videoId
// 返回: 1=已点赞, 0=取消点赞
const LIKE_SCRIPT = `
local likesKey = KEYS[1]
local dislikesKey = KEYS[2]
local hotKey = KEYS[3]
local videoId = ARGV[1]

local isDisliked = redis.call('SISMEMBER', dislikesKey, videoId)
local isLiked = redis.call('SISMEMBER', likesKey, videoId)

if isLiked == 1 then
  -- 已点赞 → 取消点赞
  redis.call('SREM', likesKey, videoId)
  redis.call('ZINCRBY', hotKey, -2, videoId)
  return 0
elseif isDisliked == 1 then
  -- 已点踩 → 切换为点赞
  redis.call('SREM', dislikesKey, videoId)
  redis.call('SADD', likesKey, videoId)
  redis.call('ZINCRBY', hotKey, 2, videoId)
  return 1
else
  -- 无操作 → 点赞
  redis.call('SADD', likesKey, videoId)
  redis.call('ZINCRBY', hotKey, 2, videoId)
  return 1
end
`

// Lua 脚本：点踩 toggle（原子操作）
// KEYS[1]: user:likes:{userId}
// KEYS[2]: user:dislikes:{userId}
// KEYS[3]: videohots
// ARGV[1]: videoId
// 返回: 1=已点踩, 0=取消点踩
const DISLIKE_SCRIPT = `
local likesKey = KEYS[1]
local dislikesKey = KEYS[2]
local hotKey = KEYS[3]
local videoId = ARGV[1]

local isLiked = redis.call('SISMEMBER', likesKey, videoId)
local isDisliked = redis.call('SISMEMBER', dislikesKey, videoId)

if isDisliked == 1 then
  -- 已点踩 → 取消
  redis.call('SREM', dislikesKey, videoId)
  return 0
elseif isLiked == 1 then
  -- 已点赞 → 切换为点踩
  redis.call('SREM', likesKey, videoId)
  redis.call('SADD', dislikesKey, videoId)
  redis.call('ZINCRBY', hotKey, -2, videoId)
  return 1
else
  -- 无操作 → 点踩（踩不加热度）
  redis.call('SADD', dislikesKey, videoId)
  return 1
end
`

// Lua 脚本：收藏 toggle
// KEYS[1]: user:collects:{userId}  — 用户收藏集合
// KEYS[2]: videohots
// ARGV[1]: videoId
// 返回: 1=已收藏, 0=取消收藏
const COLLECT_SCRIPT = `
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
`

// 加载脚本到 Redis 并返回 SHA
async function loadScripts() {
  try {
    const likeSha = await redis.script('LOAD', LIKE_SCRIPT)
    const dislikeSha = await redis.script('LOAD', DISLIKE_SCRIPT)
    const collectSha = await redis.script('LOAD', COLLECT_SCRIPT)
    console.log('Redis Lua 脚本加载成功')
    return { likeSha, dislikeSha, collectSha }
  } catch (e) {
    console.error('Redis Lua 脚本加载失败:', e.message)
    return null
  }
}

let SHAS = null

async function initLuaScripts() {
  SHAS = await loadScripts()
}

function getShas() {
  return SHAS
}

/**
 * 原子执行点赞 toggle
 * @returns 1=已点赞, 0=取消
 */
async function toggleLike(userId, videoId) {
  if (!SHAS) return null
  const keys = [
    `user:likes:${userId}`,
    `user:dislikes:${userId}`,
    'videohots',
  ]
  try {
    return await redis.evalsha(SHAS.likeSha, 3, ...keys, videoId)
  } catch (e) {
    // SHA 过期时回退到 EVAL
    if (e.message.includes('NOSCRIPT')) {
      SHAS = await loadScripts()
      return await redis.evalsha(SHAS.likeSha, 3, ...keys, videoId)
    }
    throw e
  }
}

/**
 * 原子执行点踩 toggle
 * @returns 1=已点踩, 0=取消
 */
async function toggleDislike(userId, videoId) {
  if (!SHAS) return null
  const keys = [
    `user:likes:${userId}`,
    `user:dislikes:${userId}`,
    'videohots',
  ]
  try {
    return await redis.evalsha(SHAS.dislikeSha, 3, ...keys, videoId)
  } catch (e) {
    if (e.message.includes('NOSCRIPT')) {
      SHAS = await loadScripts()
      return await redis.evalsha(SHAS.dislikeSha, 3, ...keys, videoId)
    }
    throw e
  }
}

/**
 * 原子执行收藏 toggle
 * @returns 1=已收藏, 0=取消
 */
async function toggleCollect(userId, videoId) {
  if (!SHAS) return null
  const keys = [`user:collects:${userId}`, 'videohots']
  try {
    return await redis.evalsha(SHAS.collectSha, 2, ...keys, videoId)
  } catch (e) {
    if (e.message.includes('NOSCRIPT')) {
      SHAS = await loadScripts()
      return await redis.evalsha(SHAS.collectSha, 2, ...keys, videoId)
    }
    throw e
  }
}

/**
 * 检查用户对某视频的点赞/点踩/收藏状态（O(1) 查询）
 */
async function getUserVideoStatus(userId, videoId) {
  const results = await redis.pipeline()
    .sismember(`user:likes:${userId}`, videoId)
    .sismember(`user:dislikes:${userId}`, videoId)
    .sismember(`user:collects:${userId}`, videoId)
    .exec()
  return {
    isLiked: results[0][1] === 1,
    isDisliked: results[1][1] === 1,
    isCollected: results[2][1] === 1,
  }
}

module.exports = {
  initLuaScripts,
  toggleLike,
  toggleDislike,
  toggleCollect,
  getUserVideoStatus,
}
