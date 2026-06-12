export interface ChatMessage {
  id: number
  conversationId: number
  senderId: number
  content: string
  createAt: string
  sender?: {
    id: number
    username: string
    image: string | null
  }
}

export interface ConversationInfo {
  id: number
  otherUser: {
    id: number
    username: string
    image: string | null
  }
  lastMessage: string | null
  lastMessageAt: string | null
}