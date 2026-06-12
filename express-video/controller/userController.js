const fs = require('fs')
const { promisify } = require('util')
const lodash = require('lodash')
const prisma = require('../model/index')
const { createToken } = require('../util/jwt')
const { verifyPassword, hashPassword } = require('../util/password')
const rename = promisify(fs.rename)



// 获取我的订阅（我关注了哪些频道）
exports.getchannel = async (req, res) => {
  let channelList = await prisma.subscribe.findMany({
    where: { userId: req.user.userinfo.id },
    include: { channel: true },
  })
  channelList = channelList.map(item => {
    return lodash.pick(item.channel, [
      'id',
      'username',
      'image',
      'subscribeCount',
      'channeldes',
    ])
  })
  res.status(200).json(channelList)
}

// 获取某用户的粉丝列表（谁关注了他）
exports.getsubscribe = async (req, res) => {
  let subscribeList = await prisma.subscribe.findMany({
    where: { channelId: parseInt(req.params.userId) },
    include: { user: true },
  })
  subscribeList = subscribeList.map(item => {
    return lodash.pick(item.user, [
      'id',
      'username',
      'image',
      'subscribeCount',
      'channeldes',
    ])
  })
  res.status(200).json(subscribeList)
}
//练习
// exports.get = async(req,res) => {
//   let username = req.query.name
//   if(username){
//     var user = await prisma.user.findMany({
//        where:{
//             username
//        }
//     })
//   }
//   res.status(200).json({
//     user
//   })
    
// }

exports.getuser = async (req, res) => {
  var isSubscribe = false
  // req.user 是在 util/jwt.js 的 verifyToken 中间件中挂载到 req 对象上的
  if (req.user) {
    const record = await prisma.subscribe.findFirst({
      where: {
        channelId: parseInt(req.params.userId),
        userId: req.user.userinfo.id,
      },
    })
    if (record) {
      isSubscribe = true
    }
  }

  const user = await prisma.user.findUnique({
    where: { id: parseInt(req.params.userId) },
  })
  res.status(200).json({
    ...lodash.pick(user, [
      'id',
      'username',
      'image',
      'subscribeCount',
      'channeldes',
    ]),
    isSubscribe,
  })
}

exports.unsubscribe = async (req, res) => {
  try {
    const userId = req.user.userinfo.id
    const channelId = parseInt(req.params.userId)
    if (!userId) {
      return res.status(401).json({ err: '用户信息异常，请重新登录' })
    }
    if (userId === channelId) {
      return res.status(401).json({ err: '不能取消关注自己' })
    }
    const record = await prisma.subscribe.findUnique({
      where: { userId_channelId: { userId, channelId } },
    })    
    if (record) {
      await prisma.$transaction(async (tx) => {
        await tx.subscribe.delete({ where: { id: record.id } })
        await tx.user.update({
          where: { id: channelId },
          data: { subscribeCount: { decrement: 1 } },
        })
      })
      res.status(200).json({ isSubscribe: false })
    } else {
      res.status(401).json({ err: '没有订阅了此频道' })
    }
  } catch (err) {
    console.error('Unsubscribe error:', err)
    res.status(500).json({ error: '取消关注失败，请稍后重试' })
  }
}

// 关注频道
exports.subscribe = async (req, res) => {
  try {
    const userId = req.user.userinfo.id
    const channelId = parseInt(req.params.userId)
    if (!userId) {
      return res.status(401).json({ err: '用户信息异常，请重新登录' })
    }
    if (userId === channelId) {
      return res.status(401).json({ err: '不能关注自己' })
    }

    const record = await prisma.subscribe.findUnique({
      where: { userId_channelId: { userId, channelId } },
    })
  

    if (!record) {
      await prisma.$transaction(async (tx) => {
        await tx.subscribe.create({ data: { userId, channelId } })
        await tx.user.update({
          where: { id: channelId },
          data: { subscribeCount: { increment: 1 } },
        })
      })
      res.status(200).json({ isSubscribe: true })
    } else {
      res.status(401).json({ err: '已经订阅了此频道' })
    }
  } catch (err) {
    console.error('Subscribe error:', err)
    res.status(500).json({ error: '关注失败，请稍后重试' })
  }
}

// 用户注册
exports.register = async (req, res) => {
  debugger
  try {
    const user = await prisma.user.create({
      data: {
        username: req.body.username,
        email: req.body.email,
        password: hashPassword(req.body.password),
        phone: req.body.phone,
      },
    })
    const { password: _, ...userWithoutPassword } = user
    res.status(201).json({ user: userWithoutPassword })
  } catch (err) {
    console.error('Registration error:', err)
    // 处理 Prisma 唯一约束冲突（如邮箱已被注册）
    if (err.code === 'P2002') {
      return res.status(401).json({ error: [{ msg: '邮箱或手机号已被注册' }] })
    }
    // 返回具体错误信息，方便调试
    res.status(500).json({
      error: '注册失败，请稍后重试',
      detail: {
        code: err.code || 'UNKNOWN',
        message: err.message || String(err),
        meta: err.meta || null,
      },
    })
  }
}

// 用户登录
exports.login = async (req, res) => {
  try {
    const user = await prisma.user.findFirst({
      where: { email: req.body.email },
    })
    if (!user || !verifyPassword(req.body.password, user.password)) {
      return res.status(401).json({ error: '邮箱或者密码不正确' })
    }

    const { password: _, ...dbBack } = user
    dbBack.token = await createToken(dbBack)
    res.status(200).json(dbBack)
  } catch (err) {
    console.error('Login error:', err)
    res.status(500).json({ error: '登录失败，请稍后重试' })
  }
}

// 用户修改
exports.update = async (req, res) => {
  var id = req.user.userinfo.id
  const data = { ...req.body }
  if (data.password) {
    data.password = hashPassword(data.password)
  }
  await prisma.user.update({ where: { id }, data })
  var dbBack = await prisma.user.findUnique({ where: { id } })
  res.status(202).json({ user: dbBack })
}

// 用户头像上传
exports.headimg = async (req, res) => {
  console.log(req.file)
  var fileArr = req.file.originalname.split('.')
  var filetype = fileArr[fileArr.length - 1]

  try {
    await rename(
      './public/' + req.file.filename,
      './public/' + req.file.filename + '.' + filetype
    )
    res.status(201).json({ filepath: req.file.filename + '.' + filetype })
  } catch (error) {
    res.status(500).json({ err: error })
  }
}

exports.list = async (req, res) => {
  console.log(req.user)
  res.send('/user-list')
}

exports.delete = async (req, res) => {
}
