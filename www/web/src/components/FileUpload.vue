<template>
  <div
    class="p-8 w-full max-w-md mx-auto bg-white dark:bg-gray-800 text-gray-800 dark:text-white rounded-2xl shadow-xl flex flex-col items-center space-y-6 transition-colors duration-300"
  >
    <div class="flex flex-col w-full items-center">
      <div class="flex items-center space-x-2 mb-2">
        <svg class="w-8 h-8 text-emerald-500" fill="none" stroke="currentColor" stroke-width="2"
          viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M12 16v-8m0 0l-4 4m4-4l4 4M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
        </svg>
        <h2 class="text-2xl font-extrabold dark:text-gray-100">音视频文件上传</h2>
      </div>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
        支持格式：mp3, wav, m4a, mp4, mov, mkv 等，最大 200MB
      </p>
      <div
        class="w-full border-2 border-dashed border-emerald-400 dark:border-emerald-600 rounded-xl bg-gray-50 dark:bg-gray-900 flex flex-col items-center justify-center py-8 cursor-pointer hover:bg-emerald-50 dark:hover:bg-emerald-900 transition"
        @click="triggerFileInput"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop.prevent="handleDrop"
        :class="{ 'border-emerald-600 bg-emerald-50 dark:bg-emerald-900': dragOver }"
      >
        <input
          class="hidden"
          type="file"
          ref="fileInput"
          @change="handleFileChange"
          accept=".mp3, .wav, .m4a, .wma, .aac, .ogg, .amr, .flac, .mp4, .wmv, .m4v, .flv, .rmvb, .dat, .mov, .mkv, .webm, audio/aac"
        />
        <svg class="w-12 h-12 text-emerald-400 mb-2" fill="none" stroke="currentColor" stroke-width="1.5"
          viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M12 16v-8m0 0l-4 4m4-4l4 4M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
        </svg>
        <span class="text-base font-medium text-gray-700 dark:text-gray-200">
          {{ selectedFileName || '点击或拖拽文件到此处上传' }}
        </span>
        <span v-if="selectedFile" class="text-xs text-gray-400 mt-1">
          {{ (selectedFile.size / 1024 / 1024).toFixed(2) }} MB
        </span>
      </div>

      <div v-if="isUploading" class="w-full bg-gray-300 dark:bg-gray-600 rounded-full h-3 mt-4 overflow-hidden">
        <div
          :style="{ width: uploadProgress + '%' }"
          class="bg-gradient-to-r from-emerald-400 to-emerald-600 h-3 rounded-full transition-all duration-300 animate-pulse"
        ></div>
      </div>

      <button
        class="w-full mt-6 py-2.5 bg-emerald-500 hover:bg-emerald-600 transition-transform transform hover:scale-105 hover:shadow-lg rounded-xl text-white font-bold text-lg border-none focus:outline-none focus:ring-2 focus:ring-emerald-400"
        @click="uploadFile"
        :disabled="isUploading"
      >
        <span v-if="!isUploading">开始转写</span>
        <span v-else>
          <svg class="inline w-5 h-5 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor"
              d="M4 12a8 8 0 018-8v8z"></path>
          </svg>
          上传中...
        </span>
      </button>
    </div>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'

export default {
  data() {
    return {
      selectedFile: null,
      uploadProgress: 0,
      isUploading: false,
      dragOver: false
    }
  },
  computed: {
    selectedFileName() {
      return this.selectedFile ? this.selectedFile.name : ''
    }
  },
  methods: {
    triggerFileInput() {
      this.$refs.fileInput.click()
    },
    handleFileChange(e) {
      this.selectedFile = e.target.files[0]
    },
    handleDrop(e) {
      this.dragOver = false
      const file = e.dataTransfer.files[0]
      if (file) {
        this.selectedFile = file
      }
    },
    async uploadFile() {
      if (!this.selectedFile) {
        ElMessage.error('请选择一个文件！')
        return
      }
      // 文件大小限制200MB
      if (this.selectedFile.size > 200 * 1024 * 1024) {
        ElMessage.error('文件不能超过200MB！')
        return
      }

      this.isUploading = true
      this.uploadProgress = 0

      const formData = new FormData()
      formData.append('file', this.selectedFile)

      try {
        const response = await this.$axios.post('/api/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              this.uploadProgress = parseInt(
                Math.round((progressEvent.loaded * 100) / progressEvent.total)
              )
            }
          },
          timeout: 6000000
        })

        if (response.status !== 200) {
          throw new Error('上传失败！')
        }

        ElMessage.success('文件上传成功！')

        // 发起STT任务
        const data = new FormData()
        data.append('file_id', response.data.data.file_id)
        const sttResponse = await this.$axios.post('/api/stt', data, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        if (sttResponse.status !== 200) {
          throw new Error('发起STT任务失败！')
        }

        await new Promise((resolve) => setTimeout(resolve, 1000))

        this.$router.push(`/transcripts/${sttResponse.data.data.task_id}`)
      } catch (error) {
        console.error('操作失败', error)
        ElMessage.error('操作失败，请重试！')
      } finally {
        this.isUploading = false
        this.uploadProgress = 0
      }
    }
  }
}
</script>
