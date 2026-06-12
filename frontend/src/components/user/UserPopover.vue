<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { userApi } from '@/api/user'
import { useToast } from '@/composables/useToast'

const props = defineProps<{
  user: {
    id: number
    username: string
    image: string | null
    subscribeCount?: number
    isSubscribed?: boolean
  }
}>()

const router = useRouter()
const auth = useAuthStore()
const toast = useToast()

const isSubscribed = ref(props.user.isSubscribed ?? false)
const subCount = ref(props.user.subscribeCount ?? 0)
const subLoading = ref(false)

async function toggleSubscribe() {
  if (!auth.isLoggedIn) return toast.info('请先登录')
  subLoading.value = true
  try {
    if (isSubscribed.value) {
      await userApi.unsubscribe(props.user.id)
      isSubscribed.value = false
      subCount.value--
    } else {
      await userApi.subscribe(props.user.id)
      isSubscribed.value = true
      subCount.value++
    }
  } catch (e: any) {
    const msg = e.response?.data?.err || e.response?.data?.error || '操作失败'
    toast.error(typeof msg === 'string' ? msg : '操作失败')
  } finally {
    subLoading.value = false
  }
}
</script>

<template>
  <el-popover trigger="hover" :width="220" placement="bottom-start" :show-after="300">
    <template #reference>
      <slot />
    </template>
    <div class="text-center">
      <el-avatar
        v-if="user.image"
        :src="user.image"
        :size="56"
        class="mb-2 cursor-pointer"
        @click="router.push(`/user/${user.id}`)"
      />
      <el-avatar v-else :size="56" class="mb-2 cursor-pointer" @click="router.push(`/user/${user.id}`)">
        {{ user.username?.charAt(0)?.toUpperCase() }}
      </el-avatar>
      <p
        class="font-medium text-sm cursor-pointer hover:text-blue-500"
        @click="router.push(`/user/${user.id}`)"
      >
        {{ user.username }}
      </p>
      <p class="text-xs text-gray-400 mt-1">
        {{ subCount }} 粉丝
      </p>
      <div v-if="auth.isLoggedIn && auth.user?.id !== user.id" class="flex gap-2 mt-3">
        <el-button
          :type="isSubscribed ? 'default' : 'primary'"
          size="small"
          class="flex-1"
          :loading="subLoading"
          @click="toggleSubscribe"
        >
          {{ isSubscribed ? '已关注' : '+ 关注' }}
        </el-button>
        <el-button
          type="primary"
          size="small"
          class="flex-1"
          @click="router.push(`/chat/${user.id}`)"
        >
          发消息
        </el-button>
      </div>
    </div>
  </el-popover>
</template>
