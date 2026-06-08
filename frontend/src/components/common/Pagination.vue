<script setup lang="ts">
defineProps<{
  currentPage: number
  totalPages: number
}>()
const emit = defineEmits<{ change: [page: number] }>()
</script>

<template>
  <div v-if="totalPages > 1" class="flex justify-center mt-6">
    <el-pagination
      :current-page="currentPage"
      :page-count="totalPages"
      :pager-count="7"
      background
      layout="prev, pager, next"
      @current-change="emit('change', $event)"
    />
  </div>
</template>
