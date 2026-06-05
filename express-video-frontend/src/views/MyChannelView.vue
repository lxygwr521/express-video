<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userApi } from '@/api/user'
import { videoApi } from '@/api/video'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import type { User } from '@/types/user'
import type { Video } from '@/types/video'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { UserFilled, Delete } from '@element-plus/icons-vue'

const router = useRouter()
const auth = useAuthStore()
const toast = useToast()

const profile = ref<User | null>(null)
const videos = ref<Video[]>([])
const total = ref(0)
const loading = ref(true)
const deleting = ref<number | null>(null)

async function loadData() {
  loading.value = true
  try {
    const [userRes, videoRes] = await Promise.all([
      userApi.getUser(auth.user!.id),
      videoApi.getMyVideos(),
    ])
    profile.value = { ...userRes.data, isSubscribe: userRes.data.isSubscribe }
    videos.value = videoRes.data.videos
    total.value = videoRes.data.total
  } catch (e) {
    toast.error('加载频道数据失败')
  } finally {
    loading.value = false
  }
}

async function handleDelete(videoId: number) {
  deleting.value = videoId
  try {
    await videoApi.deleteVideo(videoId)
    videos.value = videos.value.filter(v => v.id !== videoId)
    total.value--
    toast.success('视频已删除')
  } catch (e: any) {
    const msg = e?.response?.data?.err || '删除失败'
    toast.error(msg)
  } finally {
    deleting.value = null
  }
}

onMounted(loadData)
</script>

<template>
  <div v-if="loading" class="py-20"><LoadingSpinner /></div>

  <div v-else-if="profile" class="max-w-4xl mx-auto">
    <!-- 频道头部 -->
    <el-card class="mb-6" :body-style="{ padding: 0 }">
      <div class="h-32 bg-gradient-to-r from-primary to-blue-500" />
      <div class="px-6 pb-6 -mt-10 flex items-end gap-4">
        <el-avatar v-if="profile.image" :src="profile.image" :size="80" class="border-4 border-white" />
        <el-avatar v-else :size="80" class="border-4 border-white text-2xl">
          {{ profile.username?.charAt(0)?.toUpperCase() }}
        </el-avatar>
        <div class="flex-1">
          <h1 class="text-xl font-bold">{{ profile.username }}</h1>
          <p class="text-sm text-gray-500">{{ profile.subscribeCount }} 订阅 · {{ total }} 个视频</p>
        </div>
        <el-button type="primary" @click="router.push('/upload')">上传视频</el-button>
      </div>
      <div v-if="profile.channeldes" class="px-6 pb-4 text-sm text-gray-600">
        {{ profile.channeldes }}
      </div>
    </el-card>

    <!-- 我的视频列表 -->
    <el-card>
      <template #header>
        <span class="font-bold">我的视频（{{ total }}）</span>
      </template>

      <el-empty v-if="videos.length === 0" description="暂无视频，快去上传吧！">
        <el-button type="primary" @click="router.push('/upload')">上传视频</el-button>
      </el-empty>

      <div v-else class="space-y-3">
        <div
          v-for="video in videos"
          :key="video.id"
          class="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50 cursor-pointer"
          @click="router.push(`/video/${video.id}`)"
        >
          <img
            v-if="video.cover"
            :src="video.cover"
            class="w-40 h-24 object-cover rounded"
          />
          <div
            v-else
            class="w-40 h-24 bg-gray-200 rounded flex items-center justify-center text-gray-400 text-sm"
          >
            暂无封面
          </div>

          <div class="flex-1 min-w-0">
            <h3 class="font-medium truncate">{{ video.title }}</h3>
            <p v-if="video.descrption" class="text-sm text-gray-500 truncate mt-1">
              {{ video.descrption }}
            </p>
            <p class="text-xs text-gray-400 mt-1">
              {{ video.commentCount ?? 0 }} 评论 · {{ new Date(video.createAt).toLocaleDateString() }}
            </p>
          </div>

          <el-button
            type="danger"
            size="small"
            :icon="Delete"
            :loading="deleting === video.id"
            @click.stop="handleDelete(video.id)"
          >
            删除
          </el-button>
        </div>
      </div>
    </el-card>
  </div>

  <el-empty v-else description="用户不存在" />
</template>
