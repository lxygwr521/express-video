const { redis } = require('./index')
exports.hotInc = async (videoId, incNum) => {
  var data = await redis.zscore('videohots', videoId)//ZSCORE 用于获取有序集合（Sorted Set）中指定成员的分数值
  var inc = await redis.zincrby('videohots', incNum, videoId) //增加分数
  return
}

exports.hotRemove = async (videoId) => {
  return redis.zrem('videohots', videoId)
}

exports.topHots = async (num) => {
  var paixu = await redis.zrevrange('videohots', 0, num - 1, 'withscores') //返回有序集中，指定区间内的成员。其中成员的位置按分数值递减(从大到小)来排列。
  var list = []
  for (let i = 0; i < paixu.length; i += 2) {
    list.push({ videoId: paixu[i], score: paixu[i + 1] })
  }
  return list
}