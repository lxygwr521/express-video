const prisma = require('../model/index')
const { hotInc, topHots } = require('../model/redis/redishotsinc')

exports.getHots = async (req, res) => {
  var topnum = req.params.topnum
  var tops = await topHots(topnum)
  res.status(200).json({ tops })
}

// 观看+1 点赞+2 评论+2  收藏+3

exports.collect = async (req, res) => {
  const videoId = parseInt(req.params.videoId)
  const userId = req.user.userinfo._id
  const video = await prisma.video.findUnique({ where: { id: videoId } })
  if (!video) {
    return res.status(404).json({ err: '视频不存在' })
  }

  let doc = await prisma.collect.findUnique({
    where: { userId_videoId: { userId, videoId } },
  })
  if (doc) {
    return res.status(403).json({ err: '视频已被收藏' })
  }
  doc = await prisma.collect.create({ data: { userId, videoId } })

  await hotInc(videoId, 3)
  res.status(201).json({ mycollect: doc })
}

exports.likelist = async (req, res) => {
  const { pageNum = 1, pageSize = 10 } = req.body
  const userId = req.user.userinfo._id 
  const skip = (pageNum - 1) * pageSize

  const [likes, likeCount] = await Promise.all([
    prisma.videolike.findMany({
      where: { like: 1, userId },
      skip,
      take: pageSize,
      include: { video: { select: { id: true, title: true, vodvideoId: true, userId: true } } },
    }),
    prisma.videolike.count({ where: { like: 1, userId } }),
  ])
  res.status(200).json({ likes, likeCount })
}

exports.dislikevideo = async (req, res) => {
  const videoId = parseInt(req.params.videoId)
  const userId = req.user.userinfo._id
  const video = await prisma.video.findUnique({ where: { id: videoId } })
  if (!video) {
    return res.status(404).json({ err: '视频不存在' })
  }

  let isdislike = true
  let doc = await prisma.videolike.findUnique({
    where: { userId_videoId: { userId, videoId } },
  })

  if (doc) {
    if (doc.like === -1) {
      await prisma.videolike.delete({ where: { id: doc.id } })
      isdislike = false
    } else {
      doc = await prisma.videolike.update({
        where: { id: doc.id },
        data: { like: -1 },
      })
    }
  } else {
    doc = await prisma.videolike.create({
      data: { userId, videoId, like: -1 },
    })
  }

  const [likeCount, dislikeCount] = await Promise.all([
    prisma.videolike.count({ where: { videoId, like: 1 } }),
    prisma.videolike.count({ where: { videoId, like: -1 } }),
  ])

  res.status(200).json({
    ...video,
    ...{ likeCount, dislikeCount },
    isdislike,
  })
}

exports.likevideo = async (req, res) => {
  const videoId = parseInt(req.params.videoId)
  const userId = req.user.userinfo._id
  const video = await prisma.video.findUnique({ where: { id: videoId } })
  if (!video) {
    return res.status(404).json({ err: '视频不存在' })
  }

  let islike = true
  let doc = await prisma.videolike.findUnique({
    where: { userId_videoId: { userId, videoId } },
  })

  if (doc) {
    if (doc.like === 1) {
      await prisma.videolike.delete({ where: { id: doc.id } })
      islike = false
    } else {
      doc = await prisma.videolike.update({
        where: { id: doc.id },
        data: { like: 1 },
      })
      await hotInc(videoId, 2)
    }
  } else {
    doc = await prisma.videolike.create({
      data: { userId, videoId, like: 1 },
    })
    await hotInc(videoId, 2)
  }

  const [likeCount, dislikeCount] = await Promise.all([
    prisma.videolike.count({ where: { videoId, like: 1 } }),
    prisma.videolike.count({ where: { videoId, like: -1 } }),
  ])

  res.status(200).json({
    ...video,
    ...{ likeCount, dislikeCount },
    islike,
  })
}

exports.deletecomment = async (req, res) => {
  const videoId = parseInt(req.params.videoId)
  const commentId = parseInt(req.params.commentId)
  const videoInfo = await prisma.video.findUnique({ where: { id: videoId } })
  if (!videoInfo) {
    return res.status(404).json({ err: '视频不存在' })
  }
  const comment = await prisma.videocomment.findUnique({ where: { id: commentId } })
  if (!comment) {
    return res.status(404).json({ err: '评论不存在' })
  }
  if (comment.userId !== req.user.userinfo._id) {
    return res.status(403).json({ err: '评论不可删除' })
  }
  await prisma.videocomment.delete({ where: { id: commentId } })
  res.status(200).json({ err: '删除成功' })
}

exports.commentlist = async (req, res) => {
  const videoId = parseInt(req.params.videoId)
  const { pageNum = 1, pageSize = 10 } = req.body
  const skip = (pageNum - 1) * pageSize

  const [comments, commentCount] = await Promise.all([
    prisma.videocomment.findMany({
      where: { videoId },
      skip,
      take: pageSize,
      include: { user: { select: { id: true, username: true, image: true } } },
    }),
    prisma.videocomment.count({ where: { videoId } }),
  ])
  res.status(200).json({ comments, commentCount })
}

exports.comment = async (req, res) => {
  const videoId = parseInt(req.params.videoId)
  const videoInfo = await prisma.video.findUnique({ where: { id: videoId } })
  if (!videoInfo) {
    return res.status(404).json({ err: '视频不存在' })
  }
  const userId = req.user.userinfo._id

  const comment = await prisma.videocomment.create({
    data: { content: req.body.content, videoId, userId },
  })
  await hotInc(videoId, 2)
  res.status(201).json(comment)
}

exports.videolist = async (req, res) => {
  let { pageNum = 1, pageSize = 10 } = req.body
  const skip = (pageNum - 1) * pageSize
  const [videolist, getvideoCount] = await Promise.all([
    prisma.video.findMany({
      skip,
      take: pageSize,
      orderBy: { createAt: 'desc' },
      include: {
        user: { select: { id: true, username: true, image: true } },
        _count: { select: { videocomments: true } },
      },
    }),
    prisma.video.count(),
  ])

  // 将 _count.videocomments 提升为 commentCount
  const list = videolist.map(v => ({
    ...v,
    commentCount: v._count.videocomments,
    _count: undefined,
  }))

  res.status(200).json({ videolist: list, getvideoCount })
}

exports.video = async (req, res) => {
  const videoId = parseInt(req.params.videoId)
  var videoInfo = await prisma.video.findUnique({
    where: { id: videoId },
    include: {
      user: { select: { id: true, username: true, image: true } },
      _count: { select: { videocomments: true } },
    },
  })
  if (!videoInfo) {
    return res.status(404).json({ err: '视频不存在' })
  }

  // 从关联关系直接获取评论数，点赞/踩需要按 like 值分别统计
  const [likeCount, dislikeCount] = await Promise.all([
    prisma.videolike.count({ where: { videoId, like: 1 } }),
    prisma.videolike.count({ where: { videoId, like: -1 } }),
  ])
  videoInfo = {
    ...videoInfo,
    commentCount: videoInfo._count.videocomments,
    likeCount,
    dislikeCount,
    _count: undefined,
  }
  videoInfo.islike = false
  videoInfo.isDislike = false
  videoInfo.isSubscribe = false

  if (req.user.userinfo) {
    const userId = req.user.userinfo._id
    const [islike, isDislike, isSubscribe] = await Promise.all([
      prisma.videolike.findFirst({ where: { userId, videoId, like: 1 } }),
      prisma.videolike.findFirst({ where: { userId, videoId, like: -1 } }),
      prisma.subscribe.findFirst({ where: { userId, channelId: videoInfo.user._id } }),
    ])
    if (islike) videoInfo.islike = true
    if (isDislike) videoInfo.isDislike = true
    if (isSubscribe) videoInfo.isSubscribe = true
  }
  await hotInc(videoId, 1)
  res.status(200).json(videoInfo)
}

exports.createvideo = async (req, res) => {
  var body = req.body
  body.userId = req.user.userinfo._id

  try {
    var dbback = await prisma.video.create({ data: body })
    res.status(201).json({ dbback })
  } catch (error) {
    res.status(500).json({ err: error })
  }
}
