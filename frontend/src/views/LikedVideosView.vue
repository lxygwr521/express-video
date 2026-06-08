<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { videoApi } from '@/api/video'
import type { Video } from '@/types/video'
import VideoCard from '@/components/video/VideoCard.vue'
import Pagination from '@/components/common/Pagination.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const videos = ref<Video[]>([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = 10
const loading = ref(true)

async function loadPage(page = 1) {
  loading.value = true
  const res = await videoApi.getLikedVideos(page, pageSize)
  videos.value = res.data.likes.map(item => item.video)
  total.value = res.data.likeCount
  pageNum.value = page
  loading.value = false
}

onMounted(() => loadPage())
</script>

<template>
  <div class="max-w-5xl mx-auto">
    <h1 class="text-lg font-bold mb-4">我赞过的视频</h1>
    <LoadingSpinner v-if="loading" />
    <el-empty v-else-if="!videos.length" description="还没有赞过视频" />
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <VideoCard v-for="video in videos" :key="video.id" :video="video" />
    </div>
    <Pagination :current-page="pageNum" :total-pages="Math.ceil(total / pageSize)" @change="loadPage" />
  </div>
</template>
