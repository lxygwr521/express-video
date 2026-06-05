const { redis } = require('./index')
exports.hotInc = async (videoId, incNum) => {
  var data = await redis.zscore('videohots', videoId)
  if (data) {
    var inc = await redis.zincrby('videohots', incNum, videoId)
  } else {
    var inc = await redis.zadd('videohots', incNum, videoId)
  }
  return
}

exports.hotRemove = async (videoId) => {
  return redis.zrem('videohots', videoId)
}

exports.topHots = async (num) => {
  var paixu = await redis.zrevrange('videohots', 0, num - 1, 'withscores')
  var list = []
  for (let i = 0; i < paixu.length; i += 2) {
    list.push({ videoId: paixu[i], score: paixu[i + 1] })
  }
  return list
}