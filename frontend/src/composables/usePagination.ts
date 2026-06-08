import { ref, computed } from 'vue'

export function usePagination(apiCall: (page: number, size: number) => Promise<any>, pageSize = 10) {
  const pageNum = ref(1)
  const total = ref(0)
  const loading = ref(false)

  const totalPages = computed(() => Math.ceil(total.value / pageSize))

  async function loadPage(page: number) {
    loading.value = true
    try {
      const res = await apiCall(page, pageSize)
      if (res.likeCount !== undefined) total.value = res.likeCount
      if (res.commentCount !== undefined) total.value = res.commentCount
      if (res.getvideoCount !== undefined) total.value = res.getvideoCount
      if (res.total !== undefined) total.value = res.total
      pageNum.value = page
      return res
    } finally {
      loading.value = false
    }
  }

  function goTo(page: number) {
    if (page >= 1 && page <= totalPages.value) {
      loadPage(page)
    }
  }

  return { pageNum, total, totalPages, loading, loadPage, goTo }
}
