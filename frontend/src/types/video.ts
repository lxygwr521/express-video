export interface Video {
  id: number
  title: string
  descrption: string | null
  vodvideoId: string
  userId: number
  cover: string | null
  commentCount: number
  likeCount: number
  dislikeCount: number
  createAt: string
  updateAt: string
  user?: VideoUser
  islike?: boolean
  isDislike?: boolean
  isSubscribe?: boolean
  isCollect?:boolean
}

export interface VideoUser {
  id: number
  username: string
  image: string | null
}

export interface VideoForm {
  title: string
  descrption?: string
  vodvideoId: string
}

export interface Comment {
  id: number
  content: string
  videoId: number
  userId: number
  createAt: string
  updateAt: string
  user: {
    id: number
    username: string
    image: string | null
  }
}
