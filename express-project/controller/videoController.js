const prisma = require('../model/index')
const { hotInc, topHots, hotRemove } = require('../model/redis/redishotsinc')
const { getVodClient } = require('./vodController')

exports.getHots = async (req, res) => {
  var topnum = parseInt(req.params.topnum)
  var tops = await topHots(topnum)
  // 从 Redis 拿到排序后的 videoId 列表，批量查 DB 获取标题
  var videoIds = tops.map(item => parseInt(item.videoId))
  var videos = await prisma.video.findMany({
    where: { id: { in: videoIds } },
    select: { id: true, title: true },
  })
  var titleMap = {}
  videos.forEach(v => { titleMap[v.id] = v.title })
  // 按 Redis 排序顺序组装结果
  var result = tops.map(item => ({
    videoId: item.videoId,
    score: item.score,
    title: titleMap[parseInt(item.videoId)] || '',
  }))
  res.status(200).json({ tops: result })
}

// 观看+1 点赞+2 评论+2  收藏+3

exports.collect = async (req, res) => {
  const videoId = parseInt(req.params.videoId)
  const userId = req.user.userinfo.id
  const video = await prisma.video.findUnique({ where: { id: videoId } })
  if (!video) {
    return res.status(404).json({ err: '视频不存在' })
  }

  let isCollect = true
  let doc = await prisma.collect.findUnique({
    where: { userId_videoId: { userId, videoId } },
  })

  if (doc) {
    // 已收藏 → 取消收藏
    await prisma.collect.delete({ where: { id: doc.id } })
    isCollect = false
  } else {
    // 未收藏 → 收藏
    doc = await prisma.collect.create({ data: { userId, videoId } })
    await hotInc(videoId, 3)
  }

  res.status(200).json({ isCollect })
}

exports.likelist = async (req, res) => {
  const { pageNum = 1, pageSize = 10 } = req.body
  const userId = req.user.userinfo.id
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
  const userId = req.user.userinfo.id
  const video = await prisma.video.findUnique({ where: { id: videoId } })
  if (!video) {
    return res.status(404).json({ err: '视频不存在' })
  }

  let isDislike 
  let islike 
  let doc = await prisma.videolike.findUnique({
    where: { userId_videoId: { userId, videoId } },
  })

  if (doc) {
    if (doc.like === -1) {
      await prisma.videolike.delete({ where: { id: doc.id } })
      //取消点踩 点赞状态不变
      isDislike = false
    } else {
      // 从点赞切换为点踩
      doc = await prisma.videolike.update({
        where: { id: doc.id },
        data: { like: -1 },
      })
      //点踩 点赞状态取消
      isDislike = true
      islike = false
    }
  } else {
    doc = await prisma.videolike.create({
      data: { userId, videoId, like: -1 },
    })
    isDislike = true
  }

  const [likeCount, dislikeCount] = await Promise.all([
    prisma.videolike.count({ where: { videoId, like: 1 } }),
    prisma.videolike.count({ where: { videoId, like: -1 } }),
  ])

  res.status(200).json({
    ...video,
    ...{ likeCount, dislikeCount },
    islike,
    isDislike,
  })
}

exports.likevideo = async (req, res) => {
  const videoId = parseInt(req.params.videoId)
  const userId = req.user.userinfo.id
  const video = await prisma.video.findUnique({ where: { id: videoId } })
  if (!video) {
    return res.status(404).json({ err: '视频不存在' })
  }

  let islike
  let isDislike 
  let doc = await prisma.videolike.findUnique({
    where: { userId_videoId: { userId, videoId } },
  })

  if (doc) {
    if (doc.like === 1) {
      await prisma.videolike.delete({ where: { id: doc.id } })
      islike = false
    } else {
      // 从点踩切换为点赞
      doc = await prisma.videolike.update({
        where: { id: doc.id },
        data: { like: 1 },
      })
      islike = true
      isDislike = false
      await hotInc(videoId, 2)
    }
  } else {
    doc = await prisma.videolike.create({
      data: { userId, videoId, like: 1 },
    })
    islike = true
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
    isDislike,
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
  if (comment.userId !== (req.user.userinfo.id)) {
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
  const userId = req.user.userinfo.id

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
  videoInfo.isCollect = false

  if (req.user?.userinfo) {
    //查询当前用户对当前视频点赞收藏情况
    const userId = req.user.userinfo.id
    const channelId = videoInfo.user?.id || videoInfo.userId
    const [islike, isDislike, isSubscribe, isCollect] = await Promise.all([
      prisma.videolike.findFirst({ where: { userId, videoId, like: 1 } }),
      prisma.videolike.findFirst({ where: { userId, videoId, like: -1 } }),
      prisma.subscribe.findFirst({ where: { userId, channelId } }),
      prisma.collect.findFirst({ where: { userId, videoId } }),
    ])
    if (islike) videoInfo.islike = true
    if (isDislike) videoInfo.isDislike = true
    if (isSubscribe) videoInfo.isSubscribe = true
    if (isCollect) videoInfo.isCollect = true
  }
  await hotInc(videoId, 1)
  res.status(200).json(videoInfo)
}

exports.createvideo = async (req, res) => {
  var body = req.body
  body.userId = req.user.userinfo.id
 console.log(req);
 
  try {
    var dbback = await prisma.video.create({ data: body })

    // 如果未手动设置封面且是 VOD 上传，从阿里云获取封面并回写数据库
    if (!body.cover && body.vodvideoId) {
      try {
        const client = getVodClient()
        const vodRes = await client.request('GetVideoInfo', { VideoId: body.vodvideoId }, {})
        if (vodRes.Video?.CoverURL) {
          await prisma.video.update({
            where: { id: dbback.id },
            data: { cover: vodRes.Video.CoverURL },
          })
          dbback.cover = vodRes.Video.CoverURL
        }
      } catch (e) {
        console.error('获取VOD封面失败:', e.message)
      }
    }

    res.status(201).json({ dbback })
  } catch (error) {
    res.status(500).json({ err: error })
  }
}

// 获取当前用户的视频列表（我的频道）
exports.getMyVideos = async (req, res) => {
  const userId = req.user.userinfo.id
  const { pageNum = 1, pageSize = 10 } = req.body
  const skip = (pageNum - 1) * pageSize

  try {
    const [videos, total] = await Promise.all([
      prisma.video.findMany({
        where: { userId },
        skip,
        take: pageSize,
        orderBy: { createAt: 'desc' },
        include: { _count: { select: { videocomments: true } } },
      }),
      prisma.video.count({ where: { userId } }),
    ])

    const list = videos.map(v => ({
      ...v,
      commentCount: v._count.videocomments,
      _count: undefined,
    }))

    res.status(200).json({ videos: list, total })
  } catch (error) {
    res.status(500).json({ err: error })
  }
}

// 删除视频（仅限视频所有者）
exports.deleteVideo = async (req, res) => {
  const videoId = parseInt(req.params.videoId)
  const userId = req.user.userinfo.id

  try {
    const video = await prisma.video.findUnique({ where: { id: videoId } })
    if (!video) {
      return res.status(404).json({ err: '视频不存在' })
    }
    if (video.userId !== userId) {
      return res.status(403).json({ err: '无权删除此视频' })
    }

    // 事务删除视频及所有关联数据
    await prisma.$transaction(async (tx) => {
      await tx.collect.deleteMany({ where: { videoId } })
      await tx.videolike.deleteMany({ where: { videoId } })
      await tx.videocomment.deleteMany({ where: { videoId } })
      await tx.video.delete({ where: { id: videoId } })
    })

    // 清除 Redis 中的热度数据
    await hotRemove(videoId)

    // 同步删除 VOD 中的视频文件
    if (video.vodvideoId) {
      try {
        const client = getVodClient()
        await client.request('DeleteVideo', { VideoIds: video.vodvideoId }, {})
      } catch (e) {
        // VOD 删除失败记录日志但不影响整体结果（DB 已清）
        console.error('VOD 视频删除失败:', e.message)
      }
    }

    res.status(200).json({ msg: '视频已删除' })
  } catch (error) {
    res.status(500).json({ err: error })
  }
}
