<script setup lang="ts">
defineProps<{ message?: string }>()
</script>

<template>
  <el-empty :description="message || '暂无内容'" />
</template>
