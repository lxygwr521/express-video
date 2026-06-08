<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppHeader from '@/components/layout/AppHeader.vue'

const auth = useAuthStore()
onMounted(() => auth.restoreUser())
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
