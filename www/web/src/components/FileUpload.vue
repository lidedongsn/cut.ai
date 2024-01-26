<template>
  <div class="p-6 w-96 mx-auto bg-gray-200 rounded-xl shadow-md flex items-center space-x-4">
    <div class="flex flex-col w-full items-center">
      <h2 class="mb-4 text-xl font-bold text-gray-900">音视频文件上传</h2>
      <input
        class="hidden"
        type="file"
        ref="fileInput"
        @change="handleFileChange"
        style="display: none"
        accept=".mp3, .wav, .m4a, .wma, .aac, .ogg, .amr, .flac, .mp4, .wmv, .m4v, .flv, .rmvb, .dat, .mov, .mkv, .webm, audio/aac"
      />
      <!-- 自定义的矩形框，用于触发文件选择 -->
      <span
        class="block w-full px-4 py-2 border border-dashed border-gray-300 rounded-md cursor-pointer bg-gray-100 hover:bg-gray-200 transition-colors duration-300 h-16"
        @click="triggerFileInput"
      >
        <!-- 显示选择的文件名，如果没有文件，则显示默认文本 -->
        {{ selectedFileName || '选择音视频文件' }}
      </span>
      <div v-if="isUploading" class="w-full bg-gray-300 rounded-full h-2.5 dark:bg-gray-700">
        <div :style="{ width: uploadProgress + '%' }" class="bg-blue-600 h-2.5 rounded-full"></div>
      </div>

      <button
        @click="uploadFile"
        :disabled="isUploading"
        class="mt-4 px-4 py-2 bg-blue-500 text-white text-lg font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-blue-300 disabled:cursor-not-allowed"
      >
        开始转写
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
      uploadProgress: 0, // 新增上传进度变量
      isUploading: false // 新增上传状态变量
    }
  },
  computed: {
    // 计算属性用于获取选择的文件名
    selectedFileName() {
      return this.selectedFile ? this.selectedFile.name : ''
    }
  },
  methods: {
    triggerFileInput() {
      // 触发input的点击事件
      this.$refs.fileInput.click()
    },
    handleFileChange(e) {
      this.selectedFile = e.target.files[0]
    },
    async uploadFile() {
      if (!this.selectedFile) {
        ElMessage.error('请选择一个文件！')
        return
      }

      this.isUploading = true // 开始上传时设置为true

      const formData = new FormData()
      formData.append('file', this.selectedFile)

      try {
        const response = await this.$axios.post('/api/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            this.uploadProgress = parseInt(
              Math.round((progressEvent.loaded * 100) / progressEvent.total)
            )
          }
        })
        if (response.status !== 200) {
          throw new Error('上传失败！')
        }
        ElMessage({
          message: '文件上传成功！',
          type: 'success'
        })
        this.uploadProgress = 0 // 上传成功后重置进度条
        this.isUploading = false // 隐藏进度条
        // 继续发起 STT 任务请求
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

        this.$router.push(`/transcripts/${sttResponse.data.data.task_id}`); 
      } catch (error) {
        console.error('上传失败', error)
        ElMessage.error('上传失败！')
        this.isUploading = false // 发生错误时也要隐藏进度条
      }
    }
  }
}
</script>
