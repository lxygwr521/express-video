import { defineStore } from 'pinia'
import { ref } from 'vue'
import { io, Socket } from 'socket.io-client'
import { chatApi } from '@/api/chat'
import type { ChatMessage, ConversationInfo } from '@/types/chat'
//管理会话
export const useChatStore = defineStore('chat', () => {
  // --- 状态 ---
  const socket = ref<Socket | null>(null)
  const conversations = ref<ConversationInfo[]>([])
  const messages = ref<ChatMessage[]>([])
  const currentConversationId = ref<number | null>(null)
  const currentOtherUser = ref<ConversationInfo['otherUser'] | null>(null)
  const hasMore = ref(false)
  const currentPage = ref(1)
  const loading = ref(false)

  // --- Socket 连接 ---
  function connect() {
    const token = localStorage.getItem('token')
    if (!token || socket.value) return

    const wsUrl = import.meta.env.DEV ? 'http://localhost:3000' : window.location.origin
    const s = io(wsUrl, {
      auth: { token },
      transports: ['websocket', 'polling'],
    })

    s.on('new_message', ({ conversationId, message }: { conversationId: number; message: ChatMessage }) => {
      // 如果在当前会话，直接追加消息
      if (currentConversationId.value === conversationId) {
        messages.value.push(message)
      }
      // 刷新会话列表（更新 lastMessage）
      fetchConversations()
    })

    socket.value = s
  }

  function disconnect() {
    socket.value?.disconnect()
    socket.value = null
  }

  // --- 会话列表 ---
  async function fetchConversations() {
    try {
      const res = await chatApi.getConversations()
      conversations.value = res.data.conversations
    } catch (e) {
      console.error('获取会话列表失败:', e)
    }
  }

  // --- 打开会话 ---
  async function openConversation(otherUserId: number) {
    loading.value = true
    try {
      // 创建或获取会话
      const res = await chatApi.getOrCreateConversation(otherUserId)
      const convId = res.data.conversationId
      currentConversationId.value = convId
      currentPage.value = 1

      // 加入 WebSocket 房间
      socket.value?.emit('join_conversation', convId)

      // 加载消息
      const msgRes = await chatApi.getMessages(convId, 1, 30)
      messages.value = msgRes.data.messages
      hasMore.value = msgRes.data.messages.length < msgRes.data.total

      // 刷新会话列表并设置 otherUser（新会话还没在列表里）
      await fetchConversations()
      const conv = conversations.value.find(c => c.id === convId)
      if (conv) {
        currentOtherUser.value = conv.otherUser
      }
    } catch (e) {
      console.error('打开会话失败:', e)
    } finally {
      loading.value = false
    }
  }

  // --- 加载更多历史消息 ---
  async function loadMore() {
    if (!hasMore.value || !currentConversationId.value) return
    currentPage.value++
    try {
      const res = await chatApi.getMessages(currentConversationId.value!, currentPage.value, 30)
      messages.value = [...res.data.messages, ...messages.value]
      hasMore.value = messages.value.length < res.data.total
    } catch (e) {
      currentPage.value--
      console.error('加载更多失败:', e)
    }
  }

  // --- 发送消息 ---
  function sendMessage(content: string) {
    if (!content.trim() || !socket.value) return

    const payload: any = { content: content.trim() }
    if (currentConversationId.value) {
      payload.conversationId = currentConversationId.value
    } else if (currentOtherUser.value) {
      payload.recipientId = currentOtherUser.value.id
    }

    socket.value.emit('send_message', payload, (res: any) => {
      if (res?.error) {
        console.error('发送失败:', res.error)
      }
    })
  }

  // --- 关闭当前会话 ---
  function closeConversation() {
    currentConversationId.value = null
    currentOtherUser.value = null
    messages.value = []
    hasMore.value = false
    currentPage.value = 1
  }

  return {
    socket, conversations, messages,
    currentConversationId, currentOtherUser, hasMore, loading,
    connect, disconnect, fetchConversations, openConversation,
    loadMore, sendMessage, closeConversation,
  }
})
