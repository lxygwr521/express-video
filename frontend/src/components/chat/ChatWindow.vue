<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import ChatBubble from './ChatBubble.vue'

const chat = useChatStore()
const auth = useAuthStore()

const inputText = ref('')
const messagesContainer = ref<HTMLDivElement>()

// 新消息到达时自动滚底
watch(
  () => chat.messages.length,
  () => nextTick(() => scrollToBottom()),
)

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function handleSend() {
  if (!inputText.value.trim()) return
  chat.sendMessage(inputText.value)
  inputText.value = ''
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function handleScroll() {
  const el = messagesContainer.value
  if (el && el.scrollTop === 0 && chat.hasMore) {
    const prevHeight = el.scrollHeight
    chat.loadMore().then(() => {
      nextTick(() => {
        if (el) el.scrollTop = el.scrollHeight - prevHeight
      })
    })
  }
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- 顶部标题栏 -->
    <div class="flex items-center gap-3 px-4 py-3 border-b border-gray-100 bg-white shrink-0">
      <el-avatar
        v-if="chat.currentOtherUser?.image"
        :src="chat.currentOtherUser.image"
        :size="36"
      />
      <el-avatar v-else :size="36">
        {{ chat.currentOtherUser?.username?.charAt(0)?.toUpperCase() }}
      </el-avatar>
      <span class="font-medium">{{ chat.currentOtherUser?.username }}</span>
    </div>

    <!-- 消息区域 -->
    <div
      ref="messagesContainer"
      class="flex-1 overflow-y-auto px-4 py-4 bg-gray-50"
      @scroll="handleScroll"
    >
      <!-- 加载更多 -->
      <div v-if="chat.hasMore" class="text-center py-3">
        <el-button size="small" text :loading="chat.loading" @click="chat.loadMore()">
          加载更多
        </el-button>
      </div>

      <!-- 空状态 -->
      <div v-if="chat.messages.length === 0 && !chat.loading" class="text-center text-gray-400 py-20">
        发送第一条消息吧
      </div>

      <!-- 消息气泡 -->
      <ChatBubble
        v-for="msg in chat.messages"
        :key="msg.id"
        :message="msg"
        :is-mine="msg.senderId === auth.user?.id"
      />

      <!-- 加载中 -->
      <div v-if="chat.loading" class="text-center text-gray-400 py-4 text-sm">
        加载中...
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="flex items-center gap-2 px-4 py-3 border-t border-gray-100 bg-white shrink-0">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="1"
        placeholder="输入消息... (Enter 发送)"
        resize="none"
        class="flex-1"
        @keydown="handleKeydown"
      />
      <el-button type="primary" :disabled="!inputText.trim()" @click="handleSend">
        发送
      </el-button>
    </div>
  </div>
</template>
