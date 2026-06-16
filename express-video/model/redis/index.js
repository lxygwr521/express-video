const Redis = require('ioredis')
const { redisClient } = require('../../config/config.default')

const redis = new Redis(redisClient.port, redisClient.path, redisClient.options)
redis.on('error', err => {
  if (err) {
    console.log('Redis链接错误');
    console.log(err);
    redis.quit()
  }
})

redis.on('ready', async () => {
  console.log('Redis链接成功');
  // 加载 Lua 脚本到 Redis 服务器
  try {
    const { initLuaScripts } = require('./likeLua')
    await initLuaScripts()
  } catch (e) {
    console.error('Lua 脚本初始化失败:', e.message)
  }
})

exports.redis = redis
