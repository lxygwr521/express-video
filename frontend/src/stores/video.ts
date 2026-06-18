import { defineStore } from 'pinia'
import { ref } from 'vue'
import { videoApi } from '@/api/video'
import type { Video, Comment } from '@/types/video'

export const useVideoStore = defineStore('video', () => {
  const videos = ref<Video[]>([])
  const videoTotal = ref(0)
  const currentVideo = ref<Video | null>(null)
  const comments = ref<Comment[]>([])
  const commentTotal = ref(0)
  const hotVideos = ref<Array<{ videoId: string; score: string; title: string }>>([])
  const loading = ref(false)

  async function fetchVideoList(pageNum = 1, pageSize = 10) {
    loading.value = true
    const res = await videoApi.getVideoList(pageNum, pageSize)
    videos.value = res.data.videolist
    videoTotal.value = res.data.getvideoCount
    loading.value = false
    return res.data
    
  }

  async function fetchVideo(videoId: number) {
    loading.value = true
    const res = await videoApi.getVideo(videoId)
    currentVideo.value = res.data
    console.log('video',currentVideo);
    
    loading.value = false
    return res.data
  }

  async function fetchHots(num = 10) {
    const res = await videoApi.getHots(num)
    hotVideos.value = res.data.tops
    // console.log('hot',hotVideos.value);
    
  }

  async function toggleLike(videoId: number) {
    const res = await videoApi.likeVideo(videoId)
    if (currentVideo.value && currentVideo.value.id === videoId) {
      currentVideo.value = { ...currentVideo.value, ...res.data }
    }
    return res.data
  }

  async function toggleDislike(videoId: number) {
    const res = await videoApi.dislikeVideo(videoId)
    if (currentVideo.value && currentVideo.value.id === videoId) {
      currentVideo.value = { ...currentVideo.value, ...res.data }
    }
    return res.data
  }

  async function collect(videoId: number) {
    const res = await videoApi.collectVideo(videoId)
    if (currentVideo.value && currentVideo.value.id === videoId) {
      currentVideo.value = { ...currentVideo.value, ...res.data }
    }
    return res.data
  }

  async function fetchComments(videoId: number, pageNum = 1, pageSize = 10) {
    const res = await videoApi.getCommentList(videoId, pageNum, pageSize)
    comments.value = res.data.comments
    commentTotal.value = res.data.commentCount
    return res.data
  }

  async function addComment(videoId: number, content: string) {
    const res = await videoApi.createComment(videoId, content)
    if (currentVideo.value && currentVideo.value.id === videoId) {
      currentVideo.value.commentCount++
    }
    return res.data
  }

  async function removeComment(videoId: number, commentId: number) {
    const res = await videoApi.deleteComment(videoId, commentId)
    if (currentVideo.value && currentVideo.value.id === videoId) {
      currentVideo.value.commentCount--
    }
    return res.data
  }

  return {
    videos, videoTotal, currentVideo, comments, commentTotal,
    hotVideos, loading,
    fetchVideoList, fetchVideo, fetchHots,
    toggleLike, toggleDislike, collect,
    fetchComments, addComment, removeComment,
  }
})
