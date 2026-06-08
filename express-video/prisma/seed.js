const { PrismaClient } = require('@prisma/client')
const hashPassword = require('../util/password').hashPassword

const prisma = new PrismaClient()

function hash(pwd) {
  return hashPassword(pwd)
}

// 所有用户共享的密码明文
const PLAIN_PASSWORD = '123456'

const users = [
  {
    username: '程序员小王',
    email: 'xiaowang@qq.com',
    phone: '13800001001',
    channeldes: '全栈开发者，分享前端/后端/云原生技术',
    subscribeCount: 0,
  },
  {
    username: '美食博主阿丽',
    email: 'ali@qq.com',
    phone: '13800001002',
    channeldes: '带你吃遍全国美食，每周更新探店视频',
    subscribeCount: 0,
  },
  {
    username: '旅行达人老张',
    email: 'laozhang@qq.com',
    phone: '13800001003',
    channeldes: '一人一车走天涯，记录旅途中的美好瞬间',
    subscribeCount: 0,
  },
  {
    username: '音乐制作人Luna',
    email: 'luna@qq.com',
    phone: '13800001004',
    channeldes: '原创音乐 / 编曲教程 / 设备评测',
    subscribeCount: 0,
  },
  {
    username: '健身教练阿强',
    email: 'aqiang@qq.com',
    phone: '13800001005',
    channeldes: '科学健身，拒绝无效训练',
    subscribeCount: 0,
  },
]

// userId: 使用 createdUsers 数组的索引（0=第1个用户, 1=第2个用户...）
const videoData = [
  { userIdx: 0, title: 'Vue3 + TypeScript 实战教程 - 从零搭建管理后台', descrption: '本视频详细讲解了如何使用 Vue3 配合 TypeScript 从零搭建一个完整的管理后台系统，涵盖路由、状态管理、权限控制等核心内容。' },
  { userIdx: 0, title: 'Node.js 微服务架构设计与实践', descrption: '深入探讨 Node.js 微服务架构的设计思路，包括服务拆分、通信机制、熔断降级等关键概念。' },
  { userIdx: 0, title: 'Docker & K8s 容器编排入门到精通', descrption: '从 Docker 基础命令到 Kubernetes 集群管理，一套视频带你掌握容器化部署全流程。' },
  { userIdx: 1, title: '成都街头美食探店 vol.15 - 藏在巷子里的钵钵鸡', descrption: '今天带大家来一家本地人推荐的钵钵鸡，开了二十年的老店，味道真的绝了！' },
  { userIdx: 1, title: '在家复刻米其林三星甜品 - 熔岩巧克力蛋糕', descrption: '不用专业设备，普通家庭厨房也能做出米其林级别的甜品，详细步骤手把手教学。' },
  { userIdx: 1, title: '广州早茶攻略 - 10家老字号对比评测', descrption: '花了一周时间吃遍广州10家老字号早茶，从虾饺到凤爪，告诉你哪家最值得去。' },
  { userIdx: 2, title: '318川藏线自驾全纪录 Day1-Day7', descrption: '一个人一辆车，从成都出发沿318国道一路向西，记录沿途的风景、住宿和路况信息。' },
  { userIdx: 2, title: '新疆伊犁杏花沟 - 中国最美春天', descrption: '四月的伊犁，漫山遍野的杏花绽放，仿佛置身童话世界。本视频带你看遍杏花沟最美的机位。' },
  { userIdx: 2, title: '背包客穷游东南亚三国 30天花5000元', descrption: '泰国-柬埔寨-越南三国30天穷游攻略，包含签证、交通、住宿全攻略，预算友好的出境游方案。' },
  { userIdx: 3, title: '【原创】日落大道 - 完整版MV', descrption: '耗时三个月完成的全新原创单曲，融合了民谣与电子元素，希望大家喜欢。' },
  { userIdx: 3, title: 'Logic Pro X 编曲教程 - 流行歌曲制作全流程', descrption: '从旋律创作到混音母带，一步步演示一首流行歌曲的完整制作过程，适合编曲入门。' },
  { userIdx: 3, title: '千元预算搭建家庭录音棚 - 设备选购指南', descrption: '预算有限也能拥有专业品质的录音环境，推荐性价比最高的麦克风、声卡和监听设备。' },
  { userIdx: 4, title: '30天俯卧撑挑战 - 每天100个身体会发生什么变化', descrption: '记录了连续30天每天做100个俯卧撑的完整过程，包括每日数据和体型变化对比。' },
  { userIdx: 4, title: '新手健身房指南 - 拒绝社恐从认识器械开始', descrption: '第一次去健身房不知道怎么练？本视频逐一讲解每种器械的使用方法和训练部位。' },
  { userIdx: 4, title: '减脂期饮食搭配 - 吃饱也能瘦的秘诀', descrption: '减脂不等于挨饿！分享我的日常减脂餐搭配方案，包含蛋白质、碳水和脂肪的科学配比。' },
]

const covers = [
  'https://picsum.photos/seed/video1/640/360',
  'https://picsum.photos/seed/video2/640/360',
  'https://picsum.photos/seed/video3/640/360',
  'https://picsum.photos/seed/video4/640/360',
  'https://picsum.photos/seed/video5/640/360',
  'https://picsum.photos/seed/video6/640/360',
  'https://picsum.photos/seed/video7/640/360',
  'https://picsum.photos/seed/video8/640/360',
  'https://picsum.photos/seed/video9/640/360',
  'https://picsum.photos/seed/video10/640/360',
  'https://picsum.photos/seed/video11/640/360',
  'https://picsum.photos/seed/video12/640/360',
  'https://picsum.photos/seed/video13/640/360',
  'https://picsum.photos/seed/video14/640/360',
  'https://picsum.photos/seed/video15/640/360',
]

async function main() {
  console.log('开始清理旧数据...')
  await prisma.collect.deleteMany()
  await prisma.videolike.deleteMany()
  await prisma.videocomment.deleteMany()
  await prisma.subscribe.deleteMany()
  await prisma.video.deleteMany()
  await prisma.user.deleteMany()
  console.log('旧数据清理完成\n')

  // 1. 创建用户
  console.log('创建用户...')
  const createdUsers = []
  for (const u of users) {
    const user = await prisma.user.create({
      data: {
        ...u,
        password: hash(PLAIN_PASSWORD),
        image: `https://api.dicebear.com/7.x/avataaars/svg?seed=${u.username}`,
      },
    })
    createdUsers.push(user)
    console.log(`  用户创建成功: ${user.username} (id: ${user.id})`)
  }

  // 2. 创建视频
  console.log('\n创建视频...')
  const createdVideos = []
  for (let i = 0; i < videoData.length; i++) {
    const v = videoData[i]
    const video = await prisma.video.create({
      data: {
        title: v.title,
        descrption: v.descrption,
        vodvideoId: `mock-vod-${i + 1}-${Date.now()}`,
        userId: createdUsers[v.userIdx].id,
        cover: covers[i],
      },
    })
    createdVideos.push(video)
    console.log(`  视频创建成功: ${video.title}`)
  }

  // 3. 创建订阅关系
  console.log('\n创建订阅关系...')
  // 索引 = 用户下标 (0=程序员小王, 1=美食博主阿丽, 2=旅行达人老张, 3=音乐制作人Luna, 4=健身教练阿强)
  const subscribePairs = [
    [0, 1], [0, 3], [0, 4],
    [1, 2], [1, 3],
    [2, 0], [2, 1], [2, 3], [2, 4],
    [3, 0], [3, 2],
    [4, 0], [4, 1], [4, 2],
  ]
  for (const [fromIdx, toIdx] of subscribePairs) {
    await prisma.subscribe.create({
      data: { userId: createdUsers[fromIdx].id, channelId: createdUsers[toIdx].id },
    })
  }
  // 更新用户的 subscribeCount
  for (const u of createdUsers) {
    const count = await prisma.subscribe.count({ where: { channelId: u.id } })
    await prisma.user.update({ where: { id: u.id }, data: { subscribeCount: count } })
  }
  console.log(`  创建了 ${subscribePairs.length} 条订阅关系`)

  // 4. 创建评论
  console.log('\n创建评论...')
  const commentContents = [
    '讲得太好了，非常有收获！', '期待下一期更新', '这个内容很实用，已三连', '能不能出一期进阶版的？',
    '学到了学到了', '声音好清晰，画质也不错', '支持创作者！', '很详细，新手也能看懂',
    '已收藏，慢慢看', '这个地方有点没看懂，能再解释一下吗', '好厉害！', '关注了',
    '背景音乐是原创吗？很好听', '细节满满，点赞', '美食视频看饿了', '社恐终于有救了',
    '之前一直搞不懂这概念，现在清楚了', '感谢分享', '请问用什么设备拍的？画质很棒',
    '这个教程比其他UP主讲得清楚', '进度条感人', '每期必看', '来了来了',
    '下次可以讲讲这个吗', '太强了', '已点赞已投币', '封面好漂亮',
    '看得我也想去旅行了', '做得真好，继续加油',
  ]
  for (const video of createdVideos) {
    const commentCount = Math.floor(Math.random() * 4) + 1
    for (let j = 0; j < commentCount; j++) {
      const randomUser = createdUsers[Math.floor(Math.random() * createdUsers.length)]
      const content = commentContents[Math.floor(Math.random() * commentContents.length)]
      await prisma.videocomment.create({
        data: { content, videoId: video.id, userId: randomUser.id },
      })
    }
  }
  const totalComments = await prisma.videocomment.count()
  console.log(`  创建了 ${totalComments} 条评论`)

  // 5. 创建点赞/踩
  console.log('\n创建点赞记录...')
  for (const video of createdVideos) {
    const likeUserIds = new Set()
    const likeCount = Math.floor(Math.random() * 3) + 1
    for (let j = 0; j < likeCount; j++) {
      let uid
      do { uid = createdUsers[Math.floor(Math.random() * createdUsers.length)].id } while (likeUserIds.has(uid))
      likeUserIds.add(uid)
      await prisma.videolike.create({
        data: { userId: uid, videoId: video.id, like: 1 },
      })
    }
    // 随机给 0-1 个踩
    if (Math.random() > 0.5) {
      let uid
      do { uid = createdUsers[Math.floor(Math.random() * createdUsers.length)].id } while (likeUserIds.has(uid))
      likeUserIds.add(uid)
      await prisma.videolike.create({
        data: { userId: uid, videoId: video.id, like: -1 },
      })
    }
  }
  const totalLikes = await prisma.videolike.count()
  console.log(`  创建了 ${totalLikes} 条点赞/踩记录`)

  // 6. 创建收藏
  console.log('\n创建收藏记录...')
  // 索引: [用户下标, 视频下标], 原 1-5 → 0-4, 原 1-15 → 0-14
  const collectPairs = [
    [0, 3], [0, 9], [1, 0], [1, 6], [2, 4],
    [2, 7], [3, 1], [3, 12], [4, 2], [4, 13],
  ]
  for (const [uidx, vidx] of collectPairs) {
    await prisma.collect.create({ data: { userId: createdUsers[uidx].id, videoId: createdVideos[vidx].id } })
  }
  console.log(`  创建了 ${collectPairs.length} 条收藏记录`)

  console.log('\n========== 种子数据创建完成 ==========')
  console.log(`用户: ${createdUsers.length} 个`)
  console.log(`视频: ${createdVideos.length} 个`)
  console.log(`订阅: ${subscribePairs.length} 条`)
  console.log(`评论: ${totalComments} 条`)
  console.log(`点赞: ${totalLikes} 条`)
  console.log(`收藏: ${collectPairs.length} 条`)
}

main()
  .catch((e) => {
    console.error('种子数据创建失败:', e)
    process.exit(1)
  })
  .finally(() => prisma.$disconnect())
