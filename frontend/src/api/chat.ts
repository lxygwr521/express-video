import request from './request'
import type { ConversationInfo, ChatMessage } from '@/types/chat'

export const chatApi = {
  getConversations() {
    return request.get<{ conversations: ConversationInfo[] }>('/message/conversations')
  },

  getOrCreateConversation(userId: number) {
    return request.get<{ conversationId: number }>(`/message/conversation/${userId}`)
  },

  getMessages(conversationId: number, pageNum = 1, pageSize = 30) {
    return request.get<{ messages: ChatMessage[]; total: number }>(
      `/message/messages/${conversationId}?pageNum=${pageNum}&pageSize=${pageSize}`
    )
  },
}