const { Server } = require('socket.io')
const jwt = require('jsonwebtoken')
const { uuid } = require('../config/config.default')
const prisma = require('./index')

function setupWebSocket(httpServer) {
  const io = new Server(httpServer, {
    cors: { origin: '*', methods: ['GET', 'POST'] },
  })

  // JWT 鉴权中间件
  io.use(async (socket, next) => {
    const token = socket.handshake.auth?.token || socket.handshake.query?.token
    if (!token) return next(new Error('未登录'))
    try {
      const decoded = jwt.verify(token, uuid)
      socket.userId = decoded.userinfo.id
      next()
    } catch (e) {
      next(new Error('token 无效'))
    }
  })

  io.on('connection', (socket) => {
    const userId = socket.userId
    console.log(`[WS] 用户 ${userId} 已连接`)

    // 加入私聊房间
    socket.on('join_conversation', (conversationId) => {
      socket.join(`conversation:${conversationId}`)
    })

    // 发送消息
    socket.on('send_message', async (data, callback) => {
      try {
        const { conversationId, content, recipientId } = data
        if (!content?.trim()) return callback?.({ error: '消息不能为空' })

        // 如果没有 conversationId，先创建或查找会话
        let convId = conversationId
        if (!convId && recipientId) {
          const u1 = Math.min(userId, recipientId)
          const u2 = Math.max(userId, recipientId)
          let conv = await prisma.conversation.findUnique({
            where: { user1Id_user2Id: { user1Id: u1, user2Id: u2 } },
          })
          if (!conv) {
            conv = await prisma.conversation.create({
              data: { user1Id: u1, user2Id: u2 },
            })
          }
          convId = conv.id
        }
        if (!convId) return callback?.({ error: '缺少 conversationId 或 recipientId' })

        // 保存消息到数据库
        const message = await prisma.message.create({
          data: { conversationId: convId, senderId: userId, content: content.trim() },
          include: { sender: { select: { id: true, username: true, image: true } } },
        })

        // 更新会话最后消息
        await prisma.conversation.update({
          where: { id: convId },
          data: { lastMessage: content.trim(), lastMessageAt: new Date() },
        })

        // 推送给房间内所有人
        io.to(`conversation:${convId}`).emit('new_message', { conversationId: convId, message })

        callback?.({ success: true, message })
      } catch (e) {
        console.error('[WS] 发送消息失败:', e.message)
        callback?.({ error: '发送失败' })
      }
    })

    socket.on('disconnect', () => {
      console.log(`[WS] 用户 ${userId} 断开连接`)
    })
  })

  console.log('[WS] WebSocket 服务已启动')
  return io
}

module.exports = { setupWebSocket }
