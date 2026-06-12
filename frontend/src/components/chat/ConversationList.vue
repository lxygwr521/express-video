<script setup lang="ts">
import type { ConversationInfo } from '@/types/chat'

defineProps<{
  conversations: ConversationInfo[]
  activeId: number | null
}>()

const emit = defineEmits<{
  select: [conv: ConversationInfo]
}>()

function formatTime(dateStr: string | null) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="conversation-list h-full overflow-y-auto">
    <div v-if="conversations.length === 0" class="text-center text-gray-400 py-10 text-sm">
      暂无会话
    </div>
    <div
      v-for="conv in conversations"
      :key="conv.id"
      :class="[
        'flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors border-b border-gray-100',
        activeId === conv.id ? 'bg-blue-50' : ''
      ]"
      @click="emit('select', conv)"
    >
      <div class="shrink-0">
        <el-avatar v-if="conv.otherUser.image" :src="conv.otherUser.image" :size="44" />
        <el-avatar v-else :size="44">
          {{ conv.otherUser.username?.charAt(0)?.toUpperCase() }}
        </el-avatar>
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex justify-between items-baseline">
          <span class="font-medium text-sm truncate">{{ conv.otherUser.username }}</span>
          <span class="text-xs text-gray-400 shrink-0 ml-2">{{ formatTime(conv.lastMessageAt) }}</span>
        </div>
        <p class="text-xs text-gray-400 truncate mt-0.5">
          {{ conv.lastMessage || '暂无消息' }}
        </p>
      </div>
    </div>
  </div>
</template>
