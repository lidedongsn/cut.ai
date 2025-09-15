<template>
  <div class="w-full h-full flex items-center justify-center">
    <div class="max-w-6xl w-full text-center">
      <FileUpload class="mb-12 inline-block" />

      <div class="mt-8 text-left">
        <h2 class="text-2xl font-bold mb-4 border-b pb-2 dark:border-gray-700">最近任务</h2>
        <div v-if="isLoading" class="text-center text-gray-500">
          <p>正在加载任务列表...</p>
        </div>
        <div v-else-if="error" class="text-center text-red-500">
          <p>加载失败: {{ error }}</p>
        </div>
        <div v-else-if="tasks.length === 0" class="text-center text-gray-500">
          <p>没有找到已完成的转写任务。</p>
        </div>
        <div v-else>
          <div class="grid grid-cols-5 gap-6">
            <!-- Recent Tasks -->
            <div
              v-for="task in recentTasks"
              :key="task.task_id"
              class="p-4 border rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer bg-gray-50 dark:bg-gray-800 dark:border-gray-700 flex flex-col justify-between"
              @click="goToTranscript(task.task_id)"
            >
              <div>
                <h3 class="text-lg font-semibold text-blue-600 dark:text-blue-400 truncate">{{ task.file_name }}</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">时长: {{ formatDuration(task.duration) }}</p>
              </div>
              <p class="text-xs text-gray-400 dark:text-gray-500 mt-3 text-right">{{ formatDisplayDate(task.completion_time) }}</p>
            </div>
            <!-- "More" Card -->
            <a v-if="tasks.length > 4" :href="tasksUrl" target="_blank" 
              class="p-4 border rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer bg-gray-100 dark:bg-gray-800 dark:border-gray-700 flex flex-col items-center justify-center text-blue-500"
            >
              <span class="text-lg font-semibold">查看更多...</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import FileUpload from '@/components/FileUpload.vue'

export default {
  components: {
    FileUpload
  },
  data() {
    return {
      tasks: [],
      isLoading: true,
      error: null,
    }
  },
  computed: {
    recentTasks() {
      return this.tasks.slice(0, 4);
    },
    tasksUrl() {
      return this.$router.resolve({ name: 'tasks' }).href
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
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  },
  mounted() {
    this.fetchTasks()
  }
}
</script>

<style>
/* 可以在这里添加 CSS 样式 */
</style>
