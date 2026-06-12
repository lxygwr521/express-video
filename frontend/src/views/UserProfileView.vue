<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userApi } from '@/api/user'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import type { User } from '@/types/user'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { UserFilled } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToast()

const profile = ref<User | null>(null)
const isSubscribe = ref(false)
const loading = ref(true)
const subLoading = ref(false)

async function loadProfile() {
  loading.value = true
  const res = await userApi.getUser(Number(route.params.id))
  profile.value = res.data
  isSubscribe.value = res.data.isSubscribe
  loading.value = false
}

async function toggleSubscribe() {
  if (!auth.isLoggedIn) return toast.info('请先登录')
  const userId = Number(route.params.id)
  subLoading.value = true
  if (isSubscribe.value) {
    await userApi.unsubscribe(userId)
    isSubscribe.value = false
    if (profile.value) profile.value.subscribeCount--
    toast.success('已取消关注')
  } else {
    await userApi.subscribe(userId)
    isSubscribe.value = true
    if (profile.value) profile.value.subscribeCount++
    toast.success('关注成功')
  }
  subLoading.value = false
}
function sendMessages() {
  if (!auth.isLoggedIn) return toast.info('请先登录')
  router.push(`/chat/${route.params.id}`)
}
onMounted(loadProfile)
</script>

<template>
  <div v-if="loading" class="py-20"><LoadingSpinner /></div>

  <div v-else-if="profile" class="max-w-4xl mx-auto">
    <!-- 频道头部 -->
    <el-card class="mb-6" :body-style="{ padding: 0 }">
      <div class="h-32 bg-gradient-to-r from-primary to-blue-500" />
      <div class="px-6 pb-6 -mt-10 flex items-end gap-4">
        <el-avatar v-if="profile.image" :src="profile.image" :size="80" class="border-4 border-white" />
        <el-avatar v-else :size="80" class="border-4 border-white text-2xl">{{ profile.username?.charAt(0)?.toUpperCase() }}</el-avatar>
        <div class="flex-1">
          <h1 class="text-xl font-bold">{{ profile.username }}</h1>
          <p class="text-sm text-gray-500">{{ profile.subscribeCount }} 订阅</p>
        </div>
        <el-button
          v-if="auth.user?.id !== profile.id"
          :type="isSubscribe ? 'default' : 'primary'"
          :loading="subLoading"
          @click="toggleSubscribe"
        >
          {{ isSubscribe ? '已关注' : '+ 关注' }}
        </el-button>
        <el-button
          v-if="auth.user?.id !== profile.id"
          type="primary"
          :loading="subLoading"
          @click="sendMessages()"
        >
          发消息
        </el-button>
      </div>
      <div v-if="profile.channeldes" class="px-6 pb-4 text-sm text-gray-600">
        {{ profile.channeldes }}
      </div>
    </el-card>

    <el-empty v-if="!profile.channeldes && !profile.image" description="该用户还没有设置频道信息" />
  </div>

  <el-empty v-else description="用户不存在" />
</template>
