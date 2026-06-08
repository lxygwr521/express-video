<script setup lang="ts">
import { onMounted } from 'vue'
import { useVideoStore } from '@/stores/video'
import { StarFilled } from '@element-plus/icons-vue'

const store = useVideoStore()
onMounted(() => store.fetchHots(10))
</script>

<template>
  <el-card v-if="store.hotVideos.length" shadow="never">
    <template #header>
      <span class="font-bold text-sm flex items-center gap-1.5">
        <el-icon color="#f56c6c"><StarFilled /></el-icon> 热门排行
      </span>
    </template>
    <ol class="list-none m-0 p-0 space-y-2">
      <li
        v-for="(item, idx) in store.hotVideos.slice(0, 10)"
        :key="item.videoId"
        class="flex items-center gap-2 text-sm"
      >
        <el-tag size="small" :type="idx < 3 ? 'danger' : 'info'" disable-transitions class="w-5 h-5 flex items-center justify-center p-0 text-center">
          {{ idx + 1 }}
        </el-tag>
        <router-link :to="`/video/${item.videoId}`" class="text-gray-700 hover:text-primary no-underline flex-1 min-w-0">
          <span class="block truncate">{{ item.title }}</span>
        </router-link>
        <span class="text-xs text-gray-400 shrink-0">{{ item.score }} 热度</span>
      </li>
    </ol>
  </el-card>
</template>
