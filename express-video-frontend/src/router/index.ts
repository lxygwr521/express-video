import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { guest: true },
  },
  {
    path: '/video/:id',
    name: 'VideoDetail',
    component: () => import('@/views/VideoDetailView.vue'),
  },
  {
    path: '/upload',
    name: 'VideoUpload',
    component: () => import('@/views/VideoUploadView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/user/:id',
    name: 'UserProfile',
    component: () => import('@/views/UserProfileView.vue'),
  },
  {
    path: '/liked',
    name: 'LikedVideos',
    component: () => import('@/views/LikedVideosView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/channel',
    name: 'MyChannel',
    component: () => import('@/views/MyChannelView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')

  // 需要登录的页面
  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }

  // 已登录用户访问登录/注册页 → 跳转首页
  if (to.meta.guest && token) {
    return next('/')
  }

  next()
})

export default router
