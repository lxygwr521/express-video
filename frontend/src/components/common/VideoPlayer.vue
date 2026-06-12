<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { videoApi } from '@/api/video'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const props = defineProps<{ vodVideoId: string }>()

// 状态
const loading = ref(true)
const error = ref('')
const playerContainer = ref<HTMLDivElement>()

// 播放信息
const playURL = ref('')
const videoTitle = ref('')
const coverURL = ref('')
let aliplayer: any = null
let scriptLoaded = false

// 动态加载 Aliplayer SDK
function loadAliplayerScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (scriptLoaded) return resolve()
    // 检查是否已加载
    if ((window as any).Aliplayer) {
      scriptLoaded = true
      return resolve()
    }
    const script = document.createElement('script')
    script.src = 'https://g.alicdn.com/apsara-media-box/imp-web-player/2.26.1/aliplayer-min.js'
    script.onload = () => {
      scriptLoaded = true
      resolve()
    }
    script.onerror = () => reject(new Error('播放器 SDK 加载失败'))
    document.head.appendChild(script)
  })
}

// 初始化播放器
function initPlayer() {
  if (!playerContainer.value || !playURL.value) return
  // 销毁旧实例
  if (aliplayer) {
    aliplayer.dispose()
    aliplayer = null
  }

  const Aliplayer = (window as any).Aliplayer
  if (!Aliplayer) {
    error.value = '播放器组件未加载'
    return
  }

  aliplayer = new Aliplayer({
    id: 'aliplayer-container',
    source: playURL.value,
    width: '100%',
    height: '100%',
    autoplay: false,
    isLive: false,
    rePlay: false,
    playsinline: true,
    preload: true,
    controlBarVisibility: 'hover',
    useH5Prism: true,
    cover: coverURL.value || undefined,
    // 视频信息
    extraInfo: {
      crossOrigin: 'anonymous',
    },
  }, function (this: any) {
    // 播放器就绪回调
    console.log('[VideoPlayer] 播放器就绪')
  })
}

// 加载播放信息
async function loadPlayInfo() {
  if (!props.vodVideoId) {
    error.value = '无效的视频ID'
    loading.value = false
    return
  }

  loading.value = true
  error.value = ''

  try {
    // 1. 加载 SDK
    await loadAliplayerScript()

    // 2. 获取播放地址
    const res = await videoApi.getPlayInfo(props.vodVideoId)
    console.log('播放地址',res);
    
    playURL.value = res.data.defaultPlayURL
    videoTitle.value = res.data.videoBase?.Title || ''
    coverURL.value = res.data.videoBase?.CoverURL || ''

    // 3. 初始化播放器
    // 等 DOM 更新后再初始化
    loading.value = false
    await nextTick()
    initPlayer()
  } catch (e: any) {
    console.error('[VideoPlayer] 加载失败:', e)
    error.value = e?.response?.data?.error || e?.message || '视频加载失败'
    loading.value = false
  }
}

// 销毁播放器
function destroyPlayer() {
  if (aliplayer) {
    try {
      aliplayer.dispose()
    } catch (e) {
      console.warn('[VideoPlayer] 销毁播放器失败:', e)
    }
    aliplayer = null
  }
}

onMounted(loadPlayInfo)
onBeforeUnmount(destroyPlayer)

// 如果 vodVideoId 变化，重新加载
watch(() => props.vodVideoId, () => {
  destroyPlayer()
  loadPlayInfo()
})
</script>

<template>
  <div class="video-player-wrapper bg-black rounded-lg overflow-hidden">
    <!-- 加载中 -->
    <div v-if="loading" class="aspect-video flex items-center justify-center bg-gray-900">
      <LoadingSpinner />
    </div>

    <!-- 错误 -->
    <div v-else-if="error" class="aspect-video flex items-center justify-center bg-gray-900">
      <div class="text-center px-4">
        <el-icon :size="48" color="#6b7280">
          <svg fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
          </svg>
        </el-icon>
        <p class="text-gray-400 mt-2">{{ error }}</p>
      </div>
    </div>

    <!-- 播放器容器 -->
    <div
      v-else
      id="aliplayer-container" ref="playerContainer"
      class="player-container aspect-video"
    />
  </div>
</template>

<style scoped>
.video-player-wrapper {
  position: relative;
}

.player-container {
  width: 100%;
}

/* 确保 Aliplayer 填满容器 */
.player-container :deep(.prism-player) {
  width: 100% !important;
  height: 100% !important;
}

.player-container :deep(.prism-player video) {
  object-fit: contain;
}
</style>
