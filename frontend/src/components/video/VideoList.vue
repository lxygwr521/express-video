<script setup lang="ts">
import { onMounted } from 'vue'
import { useVideoStore } from '@/stores/video'
import VideoCard from './VideoCard.vue'
import Pagination from '@/components/common/Pagination.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { usePagination } from '@/composables/usePagination'

const store = useVideoStore()

const { pageNum, totalPages, loading, loadPage, goTo } = usePagination(
  (page, size) => store.fetchVideoList(page, size)
)

onMounted(() => {
  loadPage(1)  
  })
</script>

<template>
  <div>
    <LoadingSpinner v-if="loading && !store.videos.length" />
    <EmptyState v-if="!loading && !store.videos.length" message="还没有视频" />
    <div v-if="store.videos.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <VideoCard v-for="video in store.videos" :key="video.id" :video="video" />
    </div>
    <Pagination :current-page="pageNum" :total-pages="totalPages" @change="goTo" />
  </div>
</template>
