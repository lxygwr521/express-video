<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useVideoStore } from '@/stores/video'
import { useAuthStore } from '@/stores/auth'
import { userApi } from '@/api/user'
import { useToast } from '@/composables/useToast'
import type { Video } from '@/types/video'
import VideoPlayer from '@/components/common/VideoPlayer.vue'
import CommentList from '@/components/comment/CommentList.vue'
import UserPopover from '@/components/user/UserPopover.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { Pointer, CollectionTag, Star } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const videoStore = useVideoStore()
const auth = useAuthStore()
const toast = useToast()

const video = ref<Video | null>(null)
const loading = ref(true)
const likeLoading = ref(false)
const disLoading = ref(false)
const collectLoading = ref(false)
const subLoading = ref(false)

async function load() {
  loading.value = true
  video.value = await videoStore.fetchVideo(Number(route.params.id))
  loading.value = false
}

async function toggleLike() {
  if (!auth.isLoggedIn) return toast.info('请先登录')
  const videoId = Number(route.params.id)
  likeLoading.value = true
  const res = await videoStore.toggleLike(videoId)
  console.log('res',res);
  
  if (video.value) video.value = { ...video.value, ...res }
  console.log(video.value,'like');
  
  likeLoading.value = false
}

async function toggleDislike() {
  if (!auth.isLoggedIn) return toast.info('请先登录')
  const videoId = Number(route.params.id)
  disLoading.value = true
  const res = await videoStore.toggleDislike(videoId)
  console.log('res',res);
  if (video.value) video.value = { ...video.value, ...res }
  console.log(video.value,'dislike');
  
  disLoading.value = false
}

async function handleCollect() {
  if (!auth.isLoggedIn) return toast.info('请先登录')
  const videoId = Number(route.params.id)
  collectLoading.value = true
  const res = await videoStore.collect(videoId)
  console.log('collect',res);
  
  if (video.value) video.value = { ...video.value, ...res }
  toast.success(res.isCollect ? '收藏成功' : '已取消收藏')
  collectLoading.value = false
}

async function handleSubscribe() {
  if (!auth.isLoggedIn || !video.value?.userId) return
  subLoading.value = true
  try {
    if (video.value.isSubscribe) {
      const res = await userApi.unsubscribe(video.value.userId)
      console.log(res,'unsub');
      if (video.value) video.value = { ...video.value, ...res.data }
      toast.success('已取消关注')
    } else {
      const res = await userApi.subscribe(video.value.userId)
      console.log(res,'unsub');
      if (video.value) video.value = { ...video.value, ...res.data }
      toast.success('关注成功')
    }
  } catch (e: any) {
    const msg = e.response?.data?.err || e.response?.data?.error || '操作失败'
    toast.error(typeof msg === 'string' ? msg : '操作失败，请稍后重试')
  } finally {
    subLoading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div v-if="loading" class="py-20"><LoadingSpinner /></div>

  <div v-else-if="video" class="flex gap-6 max-w-7xl mx-auto">
    <!-- 左侧主体 -->
    <div class="flex-1 min-w-0 space-y-4">
      <VideoPlayer :vod-video-id="video.vodvideoId" />

      <!-- 视频信息卡片 -->
      <el-card>
        <h1 class="text-lg font-bold mb-2">{{ video.title }}</h1>
        <p v-if="video.descrption" class="text-sm text-gray-600 mb-3">{{ video.descrption }}</p>

        <!-- 作者 + 互动按钮 -->
        <div class="flex items-center justify-between flex-wrap gap-2">
          <UserPopover v-if="video.user" :user="{ id: video.user.id, username: video.user.username, image: video.user.image, subscribeCount: (video.user as any).subscribeCount, isSubscribed: video.isSubscribe }">
            <div class="flex items-center gap-2 cursor-pointer" @click="router.push(`/user/${video.userId}`)">
              <el-avatar v-if="video.user?.image" :src="video.user.image" :size="36" />
              <el-avatar v-else :size="36">{{ video.user?.username?.charAt(0)?.toUpperCase() }}</el-avatar>
              <span class="font-medium text-sm">{{ video.user?.username }}</span>
            </div>
          </UserPopover>

          <div class="flex items-center gap-2">
            <el-button
              v-if="auth.user?.id !== video.userId"
              :type="video.isSubscribe ? 'primary' : 'default'"
              size="small"
              :loading="subLoading"
              :icon="Star"
              @click="handleSubscribe"
            >
              {{ video.isSubscribe ? '已关注' : '关注' }}
            </el-button>

            <el-button
              :type="video.islike ? 'primary' : 'default'"
              size="small"
              :loading="likeLoading"
              :icon="Pointer"
              @click="toggleLike"
            >
              {{ video.likeCount }}
            </el-button>

            <el-button
              :type="video.isDislike ? 'danger' : 'default'"
              size="small"
              :loading="disLoading"
              @click="toggleDislike"
            >
              踩 {{ video.dislikeCount }}
            </el-button>

            <el-button
              :type="video.isCollect ? 'primary' : 'default'"
              size="small"
              :loading="collectLoading"
              :icon="CollectionTag"
              @click="handleCollect"
            >
              {{ video.isCollect ? '已收藏' : '收藏' }}
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- 评论区 -->
      <el-card>
        <CommentList :video-id="video.id" />
      </el-card>
    </div>

    <!-- 右侧 -->
    <aside class="hidden lg:block w-64 shrink-0">
      <el-card class="sticky top-20">
        <p class="text-sm text-gray-400 text-center">相关推荐区域</p>
      </el-card>
    </aside>
  </div>

  <el-empty v-else description="视频不存在" />
</template>
