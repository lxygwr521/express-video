<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import ConversationList from '@/components/chat/ConversationList.vue'
import ChatWindow from '@/components/chat/ChatWindow.vue'

const route = useRoute()
const chat = useChatStore()
const auth = useAuthStore()

onMounted(async () => {
  // 确保已连接 WebSocket
  if (!chat.connected && auth.isLoggedIn) {
    chat.connect()
  }
  // 加载会话列表
  await chat.fetchConversations()

  // 如果 URL 带有 userId，自动打开该会话
  const routeUserId = route.params.userId
  if (routeUserId) {
    chat.openConversation(Number(routeUserId))
  }
})

// 路由参数变化时切换会话
watch(
  () => route.params.userId,
  (newUserId) => {
    if (newUserId) chat.openConversation(Number(newUserId))
  }
)

onBeforeUnmount(() => {
  chat.closeConversation()
})

function handleSelectConversation(conv: any) {
  chat.openConversation(conv.otherUser.id)
}
</script>

<template>
  <div class="chat-view flex h-[calc(100vh-64px)] max-w-5xl mx-auto">
    <!-- 左侧会话列表 -->
    <div class="w-80 shrink-0 border-r border-gray-200 bg-white">
      <ConversationList
        :conversations="chat.conversations"
        :active-id="chat.currentConversationId"
        @select="handleSelectConversation"
      />
    </div>

    <!-- 右侧聊天区域 -->
    <div class="flex-1 min-w-0">
      <ChatWindow v-if="chat.currentConversationId && chat.currentOtherUser" />
      <div
        v-else
        class="h-full flex items-center justify-center text-gray-400 bg-gray-50"
      >
        <div class="text-center">
          <el-icon :size="64" color="#d1d5db">
            <svg fill="currentColor" viewBox="0 0 24 24">
              <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/>
            </svg>
          </el-icon>
          <p class="mt-4">选择一个会话开始聊天</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-view {
  margin-top: -1px;
}
</style>
