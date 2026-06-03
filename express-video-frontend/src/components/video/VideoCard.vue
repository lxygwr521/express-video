<script setup lang="ts">
import type { Video } from '@/types/video'
import { ChatLineSquare, Pointer } from '@element-plus/icons-vue'

defineProps<{ video: Video }>()
</script>

<template>
  <router-link :to="`/video/${video.id}`" class="no-underline">
    <el-card :body-style="{ padding: '0' }" shadow="hover" class="overflow-hidden cursor-pointer">
      <!-- 封面 -->
      <div class="aspect-video bg-gray-200 relative">
        <el-image
          v-if="video.cover"
          :src="video.cover"
          fit="cover"
          class="w-full h-full"
        />
        <div v-else class="w-full h-full flex items-center justify-center text-gray-400 text-4xl">
          <el-icon :size="48" color="#9ca3af"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></el-icon>
        </div>
        <el-tag size="small" class="absolute bottom-1 right-1 bg-black/60 border-0 text-white" disable-transitions>
          <el-icon :size="12"><ChatLineSquare /></el-icon>&nbsp;{{ video.commentCount }}
        </el-tag>
      </div>
      <!-- 信息 -->
      <div class="p-3">
        <h3 class="text-sm font-medium truncate mb-2">{{ video.title }}</h3>
        <div class="flex items-center gap-2 text-xs text-gray-500">
          <el-avatar v-if="video.user?.image" :src="video.user.image" :size="20" />
          <el-avatar v-else :size="20">{{ video.user?.username?.charAt(0)?.toUpperCase() }}</el-avatar>
          <span>{{ video.user?.username }}</span>
          <span class="ml-auto flex items-center gap-0.5">
            <el-icon :size="14"><Pointer /></el-icon>
            {{ video.likeCount }}
          </span>
        </div>
      </div>
    </el-card>
  </router-link>
</template>
