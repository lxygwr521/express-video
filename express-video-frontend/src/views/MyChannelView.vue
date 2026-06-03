<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userApi } from '@/api/user'
import type { User } from '@/types/user'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const router = useRouter()
const channels = ref<User[]>([])
const loading = ref(true)

onMounted(async () => {
  // debugger
  const res = await userApi.getMyChannels()
  channels.value = res.data
  loading.value = false
})
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <h1 class="text-lg font-bold mb-4">我的订阅</h1>
    <LoadingSpinner v-if="loading" />
    <el-empty v-else-if="!channels.length" description="还没有关注任何频道" />
    <div v-else class="space-y-2">
      <el-card
        v-for="ch in channels" :key="ch._id"
        shadow="hover"
        class="cursor-pointer"
        @click="router.push(`/user/${ch._id}`)"
      >
        <div class="flex items-center gap-3">
          <el-avatar v-if="ch.image" :src="ch.image" :size="44" />
          <el-avatar v-else :size="44">{{ ch.username?.charAt(0)?.toUpperCase() }}</el-avatar>
          <div>
            <p class="font-medium">{{ ch.username }}</p>
            <p class="text-xs text-gray-400">{{ ch.subscribeCount }} 订阅</p>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>
