<template>
  <div class="p-8 bg-white dark:bg-gray-900">
    <h1 class="text-3xl font-bold mb-6 text-gray-800 dark:text-white">所有转写任务</h1>
    <div v-if="isLoading" class="text-center text-gray-500">
      <p>正在加载任务列表...</p>
    </div>
    <div v-else-if="error" class="text-center text-red-500">
      <p>加载失败: {{ error }}</p>
    </div>
    <div v-else-if="tasks.length === 0" class="text-center text-gray-500">
      <p>没有找到已完成的转写任务。</p>
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="task in tasks"
        :key="task.task_id"
        class="p-4 border rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer bg-gray-50 dark:bg-gray-800 dark:border-gray-700 flex flex-col justify-between"
        @click="goToTranscript(task.task_id)"
      >
        <div>
          <h2 class="text-xl font-semibold text-blue-600 dark:text-blue-400 truncate">{{ task.file_name }}</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">
            时长: {{ formatDuration(task.duration) }}
          </p>
        </div>
        <p class="text-xs text-gray-400 dark:text-gray-500 mt-3 text-right">{{ formatDisplayDate(task.completion_time) }}</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      tasks: [],
      isLoading: true,
      error: null
    }
  },
  methods: {
    async fetchTasks() {
      this.isLoading = true
      try {
        const response = await this.$axios.get('/api/stt-tasks')
        if (response.data.code === 200) {
          this.tasks = response.data.data
        } else {
          throw new Error(response.data.message || '获取任务失败')
        }
      } catch (err) {
        this.error = err.message
      } finally {
        this.isLoading = false
      }
    },
    goToTranscript(taskId) {
      this.$router.push({ name: 'transcripts', params: { task_id: taskId } })
    },
    formatDuration(seconds) {
      if (seconds < 60) return `${Math.floor(seconds)}秒`
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = Math.floor(seconds % 60)
      return `${minutes}分${remainingSeconds}秒`
    },
    formatDisplayDate(isoString) {
      if (!isoString) return ''
      const date = new Date(isoString)
      return date.toLocaleString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
    }
  },
  mounted() {
    this.fetchTasks()
  }
}
</script>
