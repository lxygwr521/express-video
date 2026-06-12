<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import AppHeader from '@/components/layout/AppHeader.vue'

const auth = useAuthStore()
const chat = useChatStore()

onMounted(() => {
  auth.restoreUser()
  if (auth.isLoggedIn) chat.connect()
})

// 登录/登出时自动连接/断开 WebSocket
watch(() => auth.isLoggedIn, (loggedIn) => {
  if (loggedIn) chat.connect()
  else chat.disconnect()
})
</script>

<template>
  <el-container class="min-h-screen">
    <el-header height="60px" style="padding:0">
      <AppHeader />
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>
