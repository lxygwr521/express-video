const fs = require('fs')
const { promisify } = require('util')
const lodash = require('lodash')
const prisma = require('../model/index')
const { createToken } = require('../util/jwt')
const { verifyPassword, hashPassword } = require('../util/password')
const rename = promisify(fs.rename)



exports.getchannel = async (req, res) => {
  let channelList = await prisma.subscribe.findMany({
    where: { channelId: req.user.userinfo._id },
    include: { user: true },
  })
  channelList = channelList.map(item => {
    return lodash.pick(item.user, [
      '_id',
      'username',
      'image',
      'subscribeCount',
      'channeldes',
    ])
  })
  res.status(200).json(channelList)
}

exports.getsubscribe = async (req, res) => {
  let subscribeList = await prisma.subscribe.findMany({
    where: { userId: parseInt(req.params.userId) },
    include: { channel: true },
  })
  subscribeList = subscribeList.map(item => {
    return lodash.pick(item.channel, [
      '_id',
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
        userId: req.user.userinfo._id,
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
      '_id',
      'username',
      'image',
      'subscribeCount',
      'channeldes',
    ]),
    isSubscribe,
  })
}

exports.unsubscribe = async (req, res) => {
  const userId = req.user.userinfo._id
  const channelId = parseInt(req.params.userId)
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
    const user = await prisma.user.findUnique({ where: { id: channelId } })
    res.status(200).json(user)
  } else {
    res.status(401).json({ err: '没有订阅了此频道' })
  }
}

// 关注频道
exports.subscribe = async (req, res) => {
  const userId = req.user.userinfo._id
  const channelId = parseInt(req.params.userId)
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
    res.status(200).json({ msg: '关注成功' })
  } else {
    res.status(401).json({ err: '已经订阅了此频道' })
  }
}

// 用户注册
exports.register = async (req, res) => {
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
}

// 用户登录
exports.login = async (req, res) => {
  const user = await prisma.user.findFirst({
    where: { email: req.body.email },
  })
  if (!user || !verifyPassword(req.body.password, user.password)) {
    return res.status(402).json({ error: '邮箱或者密码不正确' })
  }

  const { password: _, ...dbBack } = user
  dbBack.token = await createToken(dbBack)
  res.status(200).json(dbBack)
}

// 用户修改
exports.update = async (req, res) => {
  var id = req.user.userinfo._id
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
