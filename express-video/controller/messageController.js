const prisma = require('../model/index')

// 获取当前用户的会话列表
exports.getConversations = async (req, res) => {
  const userId = req.user.userinfo.id
  try {
    const conversations = await prisma.conversation.findMany({
      where: {
        OR: [{ user1Id: userId }, { user2Id: userId }],
      },
      orderBy: { lastMessageAt: { sort: 'desc', nulls: 'last' } },
      include: {
        user1: { select: { id: true, username: true, image: true } },
        user2: { select: { id: true, username: true, image: true } },
        messages: {
          orderBy: { createAt: 'desc' },
          take: 1,
          select: { content: true, senderId: true, createAt: true },
        },
      },
    })

    // 格式化：otherUser 是对方用户
    const list = conversations.map(c => ({
      id: c.id,
      otherUser: c.user1Id === userId ? c.user2 : c.user1,
      lastMessage: c.lastMessage,
      lastMessageAt: c.lastMessageAt,
    }))

    res.status(200).json({ conversations: list })
  } catch (e) {
    console.error('获取会话列表失败:', e)
    res.status(500).json({ error: '获取会话列表失败' })
  }
}

// 获取某个会话的消息列表（分页）
exports.getMessages = async (req, res) => {
  const userId = req.user.userinfo.id
  const conversationId = parseInt(req.params.conversationId)
  const { pageNum = 1, pageSize = 30 } = req.query

  try {
    // 验证当前用户属于该会话
    const conv = await prisma.conversation.findUnique({ where: { id: conversationId } })
    if (!conv || (conv.user1Id !== userId && conv.user2Id !== userId)) {
      return res.status(403).json({ error: '无权访问该会话' })
    }

    const skip = (parseInt(pageNum) - 1) * parseInt(pageSize)
    const [messages, total] = await Promise.all([
      prisma.message.findMany({
        where: { conversationId },
        orderBy: { createAt: 'desc' },
        skip,
        take: parseInt(pageSize),
        include: { sender: { select: { id: true, username: true, image: true } } },
      }),
      prisma.message.count({ where: { conversationId } }),
    ])

    res.status(200).json({ messages: messages.reverse(), total })
  } catch (e) {
    console.error('获取消息列表失败:', e)
    res.status(500).json({ error: '获取消息列表失败' })
  }
}

// 创建或获取与指定用户的会话（点击"发消息"时调用）
exports.getOrCreateConversation = async (req, res) => {
  const userId = req.user.userinfo.id
  const targetUserId = parseInt(req.params.userId)

  if (userId === targetUserId) {
    return res.status(400).json({ error: '不能和自己聊天' })
  }

  try {
    const u1 = Math.min(userId, targetUserId)
    const u2 = Math.max(userId, targetUserId)

    let conv = await prisma.conversation.findUnique({
      where: { user1Id_user2Id: { user1Id: u1, user2Id: u2 } },
    })

    if (!conv) {
      conv = await prisma.conversation.create({
        data: { user1Id: u1, user2Id: u2 },
      })
    }

    res.status(200).json({ conversationId: conv.id })
  } catch (e) {
    console.error('创建会话失败:', e)
    res.status(500).json({ error: '创建会话失败' })
  }
}
