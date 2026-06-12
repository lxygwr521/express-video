<script setup lang="ts">
import type { Comment } from '@/types/video'
import { useAuthStore } from '@/stores/auth'
import { Delete } from '@element-plus/icons-vue'
import UserPopover from '@/components/user/UserPopover.vue'

const props = defineProps<{ comment: Comment }>()
const emit = defineEmits<{ deleted: [commentId: number] }>()
const auth = useAuthStore()
</script>

<template>
  <div class="flex gap-3 py-3 border-b border-gray-200 last:border-0">
    <UserPopover :user="comment.user">
      <el-avatar v-if="comment.user.image" :src="comment.user.image" :size="36" />
      <el-avatar v-else :size="36">{{ comment.user.username?.charAt(0)?.toUpperCase() }}</el-avatar>
    </UserPopover>
    <div class="flex-1 min-w-0">
      <div class="flex items-center gap-2 mb-1">
        <span class="text-sm font-medium">{{ comment.user.username }}</span>
        <span class="text-xs text-gray-400">{{ new Date(comment.createAt).toLocaleString('zh-CN') }}</span>
      </div>
      <p class="text-sm text-gray-700 break-words">{{ comment.content }}</p>
    </div>
    <el-button
      v-if="auth.user?.id === comment.userId"
      text
      type="danger"
      size="small"
      :icon="Delete"
      @click="emit('deleted', comment.id)"
    />
  </div>
</template>
