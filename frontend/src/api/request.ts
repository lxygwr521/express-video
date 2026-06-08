import axios from 'axios'
import type { AxiosError } from 'axios'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

// 请求拦截：注入 Authorization header
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：统一错误处理
request.interceptors.response.use(
  (res) => res,
  (err: AxiosError) => {
    if (err.response?.status === 402) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default request
