<template>
  <div class="p-6 w-96 mx-auto bg-white dark:bg-gray-700 text-gray-800 dark:text-white rounded-xl shadow-md flex items-center space-x-4 transition-colors duration-300">
    <div class="flex flex-col w-full items-center">
      <!-- 修复标题的深色模式文字颜色 -->
      <h2 class="mb-4 text-xl font-bold dark:text-gray-100">音视频文件上传</h2>
      
      <input
        class="hidden"
        type="file"
        ref="fileInput"
        @change="handleFileChange"
        accept=".mp3, .wav, .m4a, .wma, .aac, .ogg, .amr, .flac, .mp4, .wmv, .m4v, .flv, .rmvb, .dat, .mov, .mkv, .webm, audio/aac"
      />
      
      <!-- 自定义文件选择框：优化深色模式下的边框和背景色 -->
      <span
        class="truncate block w-full px-4 py-2 border border-dashed rounded-md cursor-pointer transition-colors duration-300 h-16
               bg-gray-100 hover:bg-gray-200 
               dark:bg-gray-900
               dark:border-gray-600 dark:text-gray-200"
        @click="triggerFileInput"
        :title="selectedFileName"
      >
        {{ selectedFileName || '选择音视频文件' }}
      </span>
      
     <!-- 进度条颜色调整：使用绿色系 -->
      <div v-if="isUploading" class="w-full bg-gray-300 dark:bg-gray-600 rounded-full h-2.5 mt-3">
        <div :style="{ width: uploadProgress + '%' }" class="bg-emerald-500 dark:bg-emerald-400 h-2.5 rounded-full transition-all duration-300"></div>
      </div>

      <!-- 按钮：优化深色模式下的悬停色和禁用色 -->
      <button
        class="w-full mt-4 py-2 transition-transform transform dark:bg-gray-900 hover:scale-105 hover:shadow-md rounded-lg text-white font-semibold border border-gray-600"
         @click="uploadFile"
        :disabled="isUploading"
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
      uploadProgress: 0,
      isUploading: false
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
    async uploadFile() {
      if (!this.selectedFile) {
        ElMessage.error('请选择一个文件！')
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

        this.$router.push(`/transcripts/${sttResponse.data.data.task_id}`); 
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