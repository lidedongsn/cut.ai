<template>
  <div class="h-screen bg-white dark:bg-gray-900 text-gray-800 dark:text-white">
    <!-- 加载状态 -->
    <div v-if="isLoading && loadingMessage" class="flex h-screen justify-center items-center">
      <div class="animate-pulse text-3xl font-bold text-center">
        {{ loadingMessage }}
        <span class="loading-animation"></span>
      </div>
    </div>

    <!-- 错误信息 -->
    <div v-else-if="error" class="p-4 bg-red-100 text-red-700 rounded-lg">
      {{ error }}
    </div>

    <!-- 显示内容 -->
    <div v-else class="relative flex-row p-10 w-full">
      <div class="text-lg font-bold mb-4">关键字</div>
      <div class="text-lg font-bold mb-4">内容概要</div>
      <div class="text-lg font-bold mb-4">原文</div>

      <!-- 如果有 segments，就分段显示 -->
      <div
        v-if="segments.length"
        class="p-4 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-white space-y-3 overflow-y-auto max-h-[70vh]"
      >
        <div v-for="(seg, idx) in segments" :key="idx" class="border-b border-gray-500 pb-2">
          <div class="text-sm text-gray-500">
            {{ formatTime(seg.start) }} - {{ formatTime(seg.end) }}
          </div>
          <div>{{ seg.text }}</div>
        </div>
      </div>

      <!-- 如果没 segments，就显示 text -->
      <div
        v-else
        class="p-4 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-white whitespace-pre-line overflow-y-auto max-h-[70vh]"
      >
        {{ text }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      text: '',
      segments: [],
      isLoading: false,
      error: null,
      loadingMessage: '',
      timer: null
    }
  },
  methods: {
    async fetchTranscript(taskId) {
      this.isLoading = true
      try {
        const response = await this.$axios.get(`/api/stt-progress/${taskId}`)
        if (response.data.code === 200) {
          const data = response.data.data
          this.text = data.text || ''
          this.segments = data.segments || []
          this.isLoading = false
          this.clearTimer()
        } else if (response.data.code === 100001) {
          this.clearTimer()
          this.timer = setTimeout(() => {
            this.fetchTranscript(taskId)
          }, 3000)
        } else {
          throw new Error(`错误: ${response.data.message}`)
        }
      } catch (err) {
        this.error = err.message || '获取转写文本时出现错误'
        this.isLoading = false
        this.clearTimer()
      }
    },
    clearTimer() {
      if (this.timer) {
        clearTimeout(this.timer)
        this.timer = null
      }
    },
    formatTime(sec) {
      const m = Math.floor(sec / 60)
      const s = Math.floor(sec % 60)
      return `${m}:${s.toString().padStart(2, '0')}`
    }
  },
  beforeUnmount() {
    document.body.style.overflowY = ''
    this.clearTimer()
  },
  mounted() {
    document.body.style.overflowY = 'hidden'
    const taskId = this.$route.params.task_id
    if (taskId) {
      this.loadingMessage = '音视频文件转写中，请稍等'
      this.fetchTranscript(taskId)
    } else {
      this.error = '没有提供任务ID'
      this.isLoading = false
    }
  }
}
</script>
