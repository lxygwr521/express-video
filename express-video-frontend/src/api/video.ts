import request from './request'
import type { Video, Comment, VideoForm } from '@/types/video'

export const videoApi = {
  // 视频列表（分页）
  getVideoList(pageNum = 1, pageSize = 10) {
    return request.post<{ videolist: Video[]; getvideoCount: number }>('/video/videolist', { pageNum, pageSize })
  },

  // 视频详情
  getVideo(videoId: number) {
    return request.get<Video>(`/video/video/${videoId}`)
  },

  // 创建视频
  createVideo(data: VideoForm) {
    return request.post<{ dbback: Video }>('/video/createvideo', data)
  },

  // 热门排行
  getHots(num: number) {
    return request.get<{ tops: Record<string, string> }>(`/video/gethots/${num}`)
  },

  // 点赞/取消点赞
  likeVideo(videoId: number) {
    return request.get<Video & { islike: boolean }>(`/video/like/${videoId}`)
  },

  // 踩/取消踩
  dislikeVideo(videoId: number) {
    return request.get<Video & { isdislike: boolean }>(`/video/dislike/${videoId}`)
  },

  // 收藏视频
  collectVideo(videoId: number) {
    return request.get(`/video/collect/${videoId}`)
  },

  // 我赞过的视频列表
  getLikedVideos(pageNum = 1, pageSize = 10) {
    return request.post<{ likes: Array<{ video: Video }>; likeCount: number }>('/video/likelist', { pageNum, pageSize })
  },

  // 评论列表
  getCommentList(videoId: number, pageNum = 1, pageSize = 10) {
    return request.post<{ comments: Comment[]; commentCount: number }>(`/video/commentlist/${videoId}`, { pageNum, pageSize })
  },

  // 发表评论
  createComment(videoId: number, content: string) {
    return request.post<Comment>(`/video/comment/${videoId}`, { content })
  },

  // 删除评论
  deleteComment(videoId: number, commentId: number) {
    return request.delete(`/video/comment/${videoId}/${commentId}`)
  },

  // 获取 VOD 上传凭证
  getVodCredential() {
    return request.get('/video/getvod')
  },

  // 获取 VOD 视频播放信息（根据 vodVideoId 获取实际播放 URL）
  getPlayInfo(vodVideoId: string) {
    return request.get<{
      videoBase: { VideoId: string; Title: string; Duration: string; CoverURL: string }
      playInfoList: Array<{
        Format: string
        PlayURL: string
        Width: number
        Height: number
        Size: number
        Bitrate: string
        Definition: string
      }>
      defaultPlayURL: string
      defaultFormat: string
      defaultDefinition: string
    }>(`/video/playinfo/${vodVideoId}`)
  },
}
