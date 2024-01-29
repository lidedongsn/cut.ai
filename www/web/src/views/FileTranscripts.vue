<template>
  <div class="h-screen gradient-bg">
    <!-- 加载状态，居中显示loadingMessage -->
    <div v-if="isLoading && loadingMessage" class="flex h-screen justify-center items-center">
      <div class="animate-pulse text-3xl font-bold text-center text-blue-800">
        {{ loadingMessage }}
        <span class="loading-animation"></span>
      </div>
    </div>

    <div v-else-if="error" class="p-4 bg-red-100 text-red-700 rounded-lg">
      {{ error }}
    </div>

    <div v-else class="relative flex-row p-10 w-full">
      <div class="text-lg font-bold mb-4">关键字</div>
      <div class="text-lg font-bold mb-4">内容概要</div>
      <div class="text-lg font-bold mb-4">原文</div>
      <div class="flex-grow p-4 rounded-lg text-gradient-bg overflow-auto h-4/5">
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
      isLoading: false,
      error: null,
      loadingMessage: '',
      timer: null // 用于存储定时器的ID
    }
  },
  methods: {
    async fetchTranscript(taskId) {
      this.isLoading = true
      console.log('开始获取转写结果...')
      try {
        const response = await this.$axios.get(`/api/stt-progress/${taskId}`)
        if (response.data.code === 200) {
          this.text = response.data.data.result.text
          this.isLoading = false
          this.clearTimer() // 获取到结果后清除定时器
        } else if (response.data.code === 100001) {
          this.clearTimer()
          this.timer = setTimeout(() => {
            this.fetchTranscript(taskId)
          }, 3000) // 每3秒重新获取一次结果
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
    }
  },
  beforeUnmount() {
    // 组件销毁前清除定时器
    document.body.style.overflowY = '' // 重新启用垂直滚动
    this.clearTimer()
  },
  mounted() {
    document.body.style.overflowY = 'hidden' // 禁用垂直滚动
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

<style scoped>
/* 在这里添加您的样式 */
@keyframes dots {
  0%,
  20% {
    content: '';
  }
  40% {
    content: '.';
  }
  60% {
    content: '..';
  }
  80%,
  100% {
    content: '...';
  }
}

.loading-animation {
  display: inline-block;
  margin-left: 4px;
  overflow: hidden; /* 防止内容溢出 */
  vertical-align: bottom; /* 与文本基线对齐 */
  animation: dots 1.5s steps(1, end) infinite;
}
.loading-animation:after {
  content: '';
  animation: dots 1.5s steps(1, end) infinite;
}
</style>
