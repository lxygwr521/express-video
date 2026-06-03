import request from './request'
import type { LoginForm, RegisterForm, UpdateUserForm, User, UserWithToken } from '@/types/user'

export const userApi = {
  // 注册
  register(data: RegisterForm) {
    return request.post<{ user: User }>('/user/registers', data)
  },

  // 登录
  login(data: LoginForm) {
    return request.post<UserWithToken>('/user/logins', data)
  },

  // 获取用户信息
  getUser(userId: number) {
    return request.get<User & { isSubscribe: boolean }>(`/user/getuser/${userId}`)
  },

  // 修改用户信息
  updateUser(data: UpdateUserForm) {
    return request.put<{ user: User }>('/user/', data)
  },

  // 关注频道
  subscribe(channelId: number) {
    return request.get<{ msg: string }>(`/user/subscribe/${channelId}`)
  },

  // 取消关注
  unsubscribe(channelId: number) {
    return request.get(`/user/unsubscribe/${channelId}`)
  },

  // 获取某用户的订阅列表
  getSubscriptions(userId: number) {
    return request.get<User[]>(`/user/getsubscribe/${userId}`)
  },

  // 获取当前用户的频道列表（我关注的）
  getMyChannels() {
    return request.get<User[]>('/user/getchannel')
  },

  // 上传头像
  uploadAvatar(file: File) {
    const fd = new FormData()
    fd.append('headimg', file)
    return request.post<{ filepath: string }>('/user/headimg', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}
