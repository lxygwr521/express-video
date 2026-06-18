const prisma = require('../model/index')

async function main() {
  // 取第一个用户作为 mock 视频的作者
  const user = await prisma.user.findFirst()
  if (!user) {
    console.error('数据库中没有用户，请先运行 seed')
    process.exit(1)
  }

  const mockVideos = [
    {
      title: 'mock 测试视频 - 前端性能优化实战',
      descrption: '这是一条 mock 数据，用于测试视频列表展示效果。讲解前端性能优化的常用手段。',
    },
    {
      title: 'mock 测试视频 - React 源码解读',
      descrption: '这是一条 mock 数据，深入 React 源码分析 Fiber 架构与调度机制。',
    },
    {
      title: 'mock 测试视频 - 算法与数据结构',
      descrption: '这是一条 mock 数据，LeetCode 高频题精讲，涵盖动态规划、回溯、双指针等。',
    },
    {
      title: 'mock 测试视频 - Python 自动化办公',
      descrption: '这是一条 mock 数据，用 Python 实现 Excel 批量处理、邮件自动发送等办公自动化场景。',
    },
    {
      title: 'mock 测试视频 - 云原生入门指南',
      descrption: '这是一条 mock 数据，从零了解 Docker、Kubernetes 和服务网格，适合初学者。',
    },
  ]

  console.log(`为用户 ${user.username} (id: ${user.id}) 创建 ${mockVideos.length} 条 mock 视频...`)

  for (const v of mockVideos) {
    const video = await prisma.video.create({
      data: {
        title: v.title,
        descrption: v.descrption,
        vodvideoId: `mock-vod-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        userId: user.id,
        cover: `https://picsum.photos/seed/${Math.random().toString(36).slice(2, 8)}/640/360`,
      },
    })
    console.log(`  创建成功: ${video.title}`)
  }

  const total = await prisma.video.count()
  console.log(`\n完成！当前数据库共有 ${total} 条视频记录`)
  await prisma.$disconnect()
}

main().catch((e) => {
  console.error('创建失败:', e)
  process.exit(1)
})
