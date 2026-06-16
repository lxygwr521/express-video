<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { videoApi } from '@/api/video'
import { useToast } from '@/composables/useToast'
import type { FormInstance, FormRules, UploadFile } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

// 阿里云 VOD 上传 SDK 类型声明（通过 index.html 中 script 标签全局加载）
declare global {
  interface Window {
    AliyunUpload: {
      Vod: new (config: VodUploadConfig) => VodUploadInstance
    }
  }
}

interface VodUploadConfig {
  userId: string
  region?: string
  partSize?: number
  parallel?: number
  retryCount?: number
  retryDuration?: number
  onUploadstarted?: (uploadInfo: VodUploadInfo) => void
  onUploadSucceed?: (uploadInfo: VodUploadInfo) => void
  onUploadFailed?: (uploadInfo: VodUploadInfo, code: string, message: string) => void
  onUploadProgress?: (uploadInfo: VodUploadInfo, totalSize: number, loadedPercent: number) => void
  onUploadTokenExpired?: (uploadInfo: VodUploadInfo) => void
  onUploadEnd?: (uploadInfo: VodUploadInfo) => void
}

interface VodUploadInstance {
  addFile(file: File, endpoint?: null, bucket?: null, object?: null, userData?: null): void
  startUpload(): void
  stopUpload(): void
  setUploadAuthAndAddress(uploadInfo: VodUploadInfo, uploadAuth: string, uploadAddress: string, videoId: string): void
  resumeUploadWithAuth(uploadAuth: string): void
  listFiles(): VodUploadInfo[]
  deleteFile(index: number): void
}

interface VodUploadInfo {
  file: File
  videoId?: string
  [key: string]: any
}

const router = useRouter()
const toast = useToast()

const formRef = ref<FormInstance>()
const form = reactive({ title: '', descrption: '' })
const videoFile = ref<File | null>(null)
const uploading = ref(false)
const uploadPercent = ref(0)
const uploadStage = ref<'idle' | 'starting' | 'uploading' | 'creating' | 'done'>('idle')
const uploadErrorHandled = ref(false)

const rules: FormRules = {
  title: [
    { required: true, message: '标题不能为空', trigger: 'blur' },
    { max: 20, message: '标题不能超过20字', trigger: 'blur' },
  ],
}

const stageText: Record<string, string> = {
  idle: '',
  starting: '正在准备上传...',
  uploading: '视频上传中...',
  creating: '正在创建视频记录...',
  done: '上传完成',
}

function handleFileChange(file: UploadFile) {
  videoFile.value = file.raw ?? null
}

function handleFileRemove() {
  videoFile.value = null
}

async function handleUpload() {
  // 1. 校验
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  if (!videoFile.value) {
    toast.error('请选择视频文件')
    return
  }

  uploading.value = true
  uploadPercent.value = 0
  uploadStage.value = 'starting'
  uploadErrorHandled.value = false

  // 用于从 onUploadstarted 回调中传递数据出来
  let uploadedVideoId = ''

  try {
    const AliyunUpload = window.AliyunUpload
    if (!AliyunUpload) {
      throw new Error('上传 SDK 未加载，请刷新页面后重试')
    }

    // 2. 创建上传实例（按官方文档：先创建 uploader，在 onUploadstarted 中获取凭证）
    const uploader = new AliyunUpload.Vod({
      userId: 'express-video-user',
      partSize: 1048576,
      parallel: 3,
      retryCount: 3,
      retryDuration: 2,

      // ★ 核心：文件准备上传时触发，在这里异步获取上传凭证
      onUploadstarted: async (uploadInfo: VodUploadInfo) => {
        console.log('[VOD] onUploadstarted:', uploadInfo.file.name)
        try {
          const res = await videoApi.getVodCredential(form.title, uploadInfo.file.name)
          const { VideoId, UploadAddress, UploadAuth } = res.data
          uploadedVideoId = VideoId
          // 设置凭证后 SDK 自动继续上传
          uploader.setUploadAuthAndAddress(uploadInfo, UploadAuth, UploadAddress, VideoId)
        } catch (e: any) {
          console.error('[VOD] 获取上传凭证失败:', e)
          toast.error('获取上传凭证失败')
          uploading.value = false
          uploadStage.value = 'idle'
        }
      },

      onUploadProgress: (_uploadInfo: VodUploadInfo, _totalSize: number, loadedPercent: number) => {
        uploadStage.value = 'uploading'
        uploadPercent.value = Math.ceil(loadedPercent * 100)
      },

      onUploadSucceed: (_uploadInfo: VodUploadInfo) => {
        console.log('[VOD] 上传成功')
        uploadPercent.value = 100
      },

      onUploadFailed: (_uploadInfo: VodUploadInfo, code: string, message: string) => {
        console.error('[VOD] 上传失败:', code, message)
        uploadErrorHandled.value = true
        toast.error(message || '视频上传失败')
        uploading.value = false
        uploadStage.value = 'idle'
      },

      onUploadTokenExpired: async (uploadInfo: VodUploadInfo) => {
        console.log('[VOD] 凭证过期，重新获取')
        try {
          const res = await videoApi.getVodCredential(form.title, uploadInfo.file.name)
          uploader.resumeUploadWithAuth(res.data.UploadAuth)
        } catch (e) {
          console.error('[VOD] 刷新凭证失败:', e)
        }
      },

      onUploadEnd: () => {
        console.log('[VOD] 所有文件上传结束')
      },
    })

    // 3. 添加文件并开始上传
    uploader.addFile(videoFile.value)
    uploader.startUpload()

    // 4. 等待上传完成（通过轮询 + Promise 包装）
    await new Promise<void>((resolve, reject) => {
      const checkDone = setInterval(() => {
        if (!uploading.value) {
          // uploading 被 onUploadFailed 设为 false 表示失败
          clearInterval(checkDone)
          reject(new Error('上传已中断'))
        } else if (uploadPercent.value >= 100 && uploadedVideoId) {
          clearInterval(checkDone)
          resolve()
        }
      }, 300)
    })

    // 5. 创建数据库记录
    uploadStage.value = 'creating'
    const createRes = await videoApi.createVideo({
      title: form.title,
      descrption: form.descrption || undefined,
      vodvideoId: uploadedVideoId,
    })
    const videoId = createRes.data.dbback.id

    // 6. 轮询等待 VOD 截图回调更新封面（最多等 30 秒）
    let coverReady = false
    for (let i = 0; i < 10; i++) {
      await new Promise(r => setTimeout(r, 1000))
      const detail = await videoApi.getVideo(videoId)
      if (detail.data.cover) {
        coverReady = true
        break
      }
    }
    if (coverReady) {
      uploadStage.value = 'done'
      toast.success('视频发布成功！')
      setTimeout(() => {
      router.push(`/video/${videoId}`)
    }, 600)
    }


  } catch (e: any) {
    if (!uploadErrorHandled.value) {
      const msg = e?.response?.data?.error || e?.message || '上传失败'
      toast.error(typeof msg === 'string' ? msg : '上传失败，请重试')
    }
  } finally {
    uploading.value = false
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

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="handleUpload">
        <!-- 视频标题 -->
        <el-form-item label="视频标题" prop="title">
          <el-input v-model="form.title" placeholder="最多20字" maxlength="20" show-word-limit :disabled="uploading" />
        </el-form-item>

        <!-- 视频描述 -->
        <el-form-item label="视频描述">
          <el-input
            v-model="form.descrption"
            type="textarea"
            :rows="3"
            placeholder="视频简介（选填）"
            :disabled="uploading"
          />
        </el-form-item>

        <!-- 选择视频文件 -->
        <el-form-item label="视频文件">
          <el-upload
            drag
            :auto-upload="false"
            :limit="1"
            accept="video/*"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :disabled="uploading"
          >
            <el-icon :size="40" color="#c0c4cc"><UploadFilled /></el-icon>
            <div class="text-sm text-gray-500 mt-2">
              点击或将视频文件拖拽至此区域
            </div>
            <template #tip>
              <p class="text-xs text-gray-400 mt-1">支持常见视频格式，单文件上传</p>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 上传进度 -->
        <div
          v-if="uploadStage !== 'idle'"
          class="mb-4 p-3 bg-blue-50 rounded-lg text-sm"
        >
          <p class="text-blue-700 font-medium mb-1">{{ stageText[uploadStage] }}</p>
          <el-progress
            v-if="uploadStage === 'uploading' || uploadPercent > 0"
            :percentage="uploadPercent"
            :stroke-width="8"
            :show-text="true"
          />
        </div>

        <!-- 提交按钮 -->
        <el-form-item>
          <el-button
            type="primary"
            :loading="uploading"
            :disabled="!videoFile || uploading"
            class="w-full"
            size="large"
            @click="handleUpload"
          >
            {{ uploading ? stageText[uploadStage] : '开始上传' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
