const OSS = require('ali-oss')

const client = new OSS({
  region: process.env.OSS_REGION || 'oss-cn-beijing',
  accessKeyId: process.env.ALIYUN_ACCESS_KEY_ID,
  accessKeySecret: process.env.ALIYUN_ACCESS_KEY_SECRET,
  bucket: process.env.OSS_BUCKET,
})

module.exports = client
