<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const auth = useAuthStore()
const toast = useToast()

const formRef = ref<FormInstance>()
const form = reactive({ email: '', password: '' })
const loading = ref(false)

const rules: FormRules = {
  email: [
    { required: true, message: '邮箱不能为空', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '密码不能为空', trigger: 'blur' },
  ],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await auth.login(form)
    toast.success('登录成功')
    router.push('/')
  } catch (e: any) {
    toast.error(e.response?.data?.error || '邮箱或密码不正确')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-sm mx-auto mt-16">
    <el-card>
      <template #header><h1 class="text-xl font-bold text-center">登录</h1></template>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="handleLogin">
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" class="w-full">登录</el-button>
        </el-form-item>
      </el-form>
      <p class="text-center text-sm text-gray-500">
        还没有账号？ <router-link to="/register" class="text-primary">去注册</router-link>
      </p>
    </el-card>
  </div>
</template>
