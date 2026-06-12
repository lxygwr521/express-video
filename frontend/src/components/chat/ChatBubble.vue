<script setup lang="ts">
import type { ChatMessage } from '@/types/chat'

const props = defineProps<{
  message: ChatMessage
  isMine: boolean
}>()

function formatTime(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div :class="['flex gap-2 mb-4', isMine ? 'flex-row-reverse' : '']">
    <!-- 头像 -->
    <el-avatar v-if="message.sender?.image" :src="message.sender.image" :size="32" />
    <el-avatar v-else :size="32">
      {{ message.sender?.username?.charAt(0)?.toUpperCase() }}
    </el-avatar>

    <!-- 气泡 -->
    <div :class="['max-w-[70%]', isMine ? 'items-end' : 'items-start']">
      <div
        :class="[
          'px-3 py-2 rounded-lg text-sm leading-relaxed',
          isMine ? 'bg-blue-500 text-white rounded-tr-sm' : 'bg-gray-100 text-gray-800 rounded-tl-sm'
        ]"
      >
        {{ message.content }}
      </div>
      <span class="text-xs text-gray-400 mt-1 block">{{ formatTime(message.createAt) }}</span>
    </div>
  </div>
</template>
