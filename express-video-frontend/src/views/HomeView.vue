<script setup lang="ts">
import VideoList from '@/components/video/VideoList.vue'
import HotVideoRank from '@/components/video/HotVideoRank.vue'
</script>

<template>
  <div class="flex gap-6 max-w-7xl mx-auto">
    <div class="flex-1 min-w-0">
      <h2 class="text-lg font-bold mb-4">最新视频</h2>
      <VideoList />
    </div>
    <aside class="hidden lg:block w-64 shrink-0">
      <div class="sticky top-20">
        <HotVideoRank />
      </div>
    </aside>
  </div>
</template>
