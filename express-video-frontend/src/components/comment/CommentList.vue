<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { videoApi } from '@/api/video'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import type { Comment } from '@/types/video'
import CommentItem from './CommentItem.vue'
import Pagination from '@/components/common/Pagination.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { ChatDotSquare } from '@element-plus/icons-vue'

const props = defineProps<{ videoId: number }>()
const auth = useAuthStore()
const toast = useToast()

const comments = ref<Comment[]>([])
const commentTotal = ref(0)
const pageNum = ref(1)
const pageSize = 10
const totalPages = ref(0)
const newComment = ref('')
const submitting = ref(false)

async function loadComments(page = 1) {
  const res = await videoApi.getCommentList(props.videoId, page, pageSize)
  comments.value = res.data.comments
  commentTotal.value = res.data.commentCount
  pageNum.value = page
  totalPages.value = Math.ceil(res.data.commentCount / pageSize)
}

async function handleAddComment() {
  if (!newComment.value.trim()) return
  submitting.value = true
  await videoApi.createComment(props.videoId, newComment.value.trim())
  newComment.value = ''
  await loadComments(pageNum.value)
  submitting.value = false
}

async function handleDelete(commentId: number) {
  await videoApi.deleteComment(props.videoId, commentId)
  toast.success('删除成功')
  await loadComments(pageNum.value)
}

onMounted(() => loadComments())
</script>

<template>
  <div>
    <h3 class="font-bold text-sm mb-3 flex items-center gap-1">
      <el-icon><ChatDotSquare /></el-icon> 评论 ({{ commentTotal }})
    </h3>

    <!-- 发评论 -->
    <div v-if="auth.isLoggedIn" class="flex gap-2 mb-4">
      <el-input
        v-model="newComment"
        placeholder="写下你的评论..."
        @keyup.enter="handleAddComment"
        clearable
      />
      <el-button type="primary" :disabled="submitting || !newComment.trim()" @click="handleAddComment">
        {{ submitting ? '发表中...' : '发表' }}
      </el-button>
    </div>
    <p v-else class="text-sm text-gray-400 mb-4">
      <router-link to="/login" class="text-primary">登录</router-link> 后发表评论
    </p>

    <EmptyState v-if="!comments.length" message="暂无评论" />
    <div v-else class="mb-4">
      <CommentItem v-for="c in comments" :key="c.id" :comment="c" @deleted="handleDelete" />
    </div>

    <Pagination :current-page="pageNum" :total-pages="totalPages" @change="loadComments" />
  </div>
</template>
