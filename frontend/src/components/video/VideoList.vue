<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useVideoStore } from '@/stores/video'
import VideoCard from './VideoCard.vue'
import Pagination from '@/components/common/Pagination.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const store = useVideoStore()
const pageSize = 10
const pageNum = ref(1)
const total = ref(0)
const totalPages = computed(() => Math.ceil(total.value / pageSize))

async function loadPage(page: number) {
  const res = await store.fetchVideoList(page, pageSize)
  total.value = res.getvideoCount
  pageNum.value = page
}

function goTo(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    loadPage(page)
  }
}

onMounted(() => {
  loadPage(1)
})
</script>

<template>
  <div>
    <LoadingSpinner v-if="store.loading && !store.videos.length" />
    <EmptyState v-if="!store.loading && !store.videos.length" message="还没有视频" />
    <div v-if="store.videos.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <VideoCard v-for="video in store.videos" :key="video.id" :video="video" />
    </div>
    <Pagination :current-page="pageNum" :total-pages="totalPages" @change="goTo" />
  </div>
</template>
