<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import { VideoCamera, User, SwitchButton } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToast()

function isActive(path: string) {
  return route.path === path
}

function handleLogout() {
  auth.logout()
  toast.success('已退出登录')
  router.push('/login')
}
</script>

<template>
  <div class="h-full flex items-center justify-between px-5 bg-white border-b border-gray-200">
    <!-- Logo -->
    <router-link to="/" class="flex items-center gap-2 no-underline">
      <el-icon :size="24" color="#409EFF"><VideoCamera /></el-icon>
      <span class="text-lg font-bold text-gray-800">ExpressVideo</span>
    </router-link>

    <!-- Nav -->
    <div class="flex items-center gap-3">
      <el-button
        text
        :type="isActive('/') ? 'primary' : undefined"
        @click="router.push('/')"
      >首页</el-button>

      <template v-if="auth.isLoggedIn">
        <el-button
          text
          :type="isActive('/upload') ? 'primary' : undefined"
          @click="router.push('/upload')"
        >
          上传视频
        </el-button>
        <el-button
          text
          :type="isActive('/subscribe') ? 'primary' : undefined"
          @click="router.push('/subscribe')"
        >我的订阅</el-button>
        <el-button
          text
          :type="isActive('/liked') ? 'primary' : undefined"
          @click="router.push('/liked')"
        >赞过</el-button>

        <el-dropdown trigger="click">
          <span class="flex items-center gap-2 cursor-pointer">
            <el-avatar v-if="auth.user?.image" :src="auth.user.image" :size="32" />
            <el-avatar v-else :size="32">{{ auth.user?.username?.charAt(0)?.toUpperCase() }}</el-avatar>
            <span class="text-sm">{{ auth.user?.username }}</span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="router.push('/channel')">
                <el-icon><User /></el-icon> 我的频道
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>

      <template v-else>
        <el-button :type="isActive('/login') ? 'primary': undefined" text @click="router.push('/login')">登录</el-button>
        <el-button :type="isActive('/register') ? 'primary': undefined" text  @click="router.push('/register')">注册</el-button>
      </template>
    </div>
  </div>
</template>
