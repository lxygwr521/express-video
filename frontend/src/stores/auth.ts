import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi } from '@/api/user'
import type { User, LoginForm, RegisterForm } from '@/types/user'
//管理用户的登录/登出状态 用户token的存储
export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isLoggedIn = computed(() => !!user.value)

  function setUser(u: User) {
    user.value = u
    localStorage.setItem('user', JSON.stringify(u))
  }

  function restoreUser() {
    const stored = localStorage.getItem('user')
    if (stored) {
      try {
        user.value = JSON.parse(stored)
      } catch {
        // corrupt data
      }
    }
  }

  async function login(data: LoginForm) {
    const res = await userApi.login(data)
    const u = res.data
    localStorage.setItem('token', u.token)
    const { token: _, ...userData } = u
    setUser(userData as User)
    return u
  }

  async function register(data: RegisterForm) {
    const res = await userApi.register(data)
    return res.data
  }

  function logout() {
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { user, isLoggedIn, login, register, logout, setUser, restoreUser }
})
