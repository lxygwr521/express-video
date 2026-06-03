<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { videoApi } from '@/api/video'
import { useToast } from '@/composables/useToast'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const toast = useToast()

const formRef = ref<FormInstance>()
const form = reactive({ title: '', descrption: '', vodvideoId: '', cover: '' })
const uploading = ref(false)

const rules: FormRules = {
  title: [
    { required: true, message: '标题不能为空', trigger: 'blur' },
    { max: 20, message: '标题不能超过20字', trigger: 'blur' },
  ],
  vodvideoId: [{ required: true, message: 'VOD视频ID不能为空', trigger: 'blur' }],
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  uploading.value = true
  try {
    const res = await videoApi.createVideo({
      title: form.title,
      descrption: form.descrption || undefined,
      vodvideoId: form.vodvideoId,
      cover: form.cover || undefined,
    })
    toast.success('创建成功')
    router.push(`/video/${res.data.dbback.id}`)
  } catch {
    toast.error('创建失败')
  } finally {
    uploading.value = false
  }
}

async function getVodToken() {
  try {
    await videoApi.getVodCredential()
    toast.info('VOD凭证已获取，查看控制台')
  } catch {
    toast.error('获取VOD凭证失败')
  }
}
</script>

<template>
  <div class="max-w-lg mx-auto">
    <el-card>
      <template #header>
        <div class="flex items-center justify-between">
          <h1 class="text-lg font-bold">上传视频</h1>
          <button class="text-xl leading-none text-gray-400 hover:text-gray-600" @click="router.back()">&times;</button>
        </div>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="handleSubmit">
        <el-form-item label="视频标题" prop="title">
          <el-input v-model="form.title" placeholder="最多20字" maxlength="20" show-word-limit />
        </el-form-item>
        <el-form-item label="视频描述">
          <el-input v-model="form.descrption" type="textarea" :rows="3" placeholder="视频简介（选填）" />
        </el-form-item>
        <el-form-item label="VOD 视频 ID" prop="vodvideoId">
          <el-input v-model="form.vodvideoId" placeholder="阿里云VOD上传后的VideoId">
            <template #append>
              <el-button @click="getVodToken">获取凭证</el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="封面图 URL">
          <el-input v-model="form.cover" placeholder="封面图片链接（选填）" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="uploading" class="w-full">提交视频</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
