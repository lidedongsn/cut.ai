<template>
  <div class="bg-white dark:bg-gray-900 text-gray-800 dark:text-white h-full">
    <!-- 全局加载状态 -->
    <div v-if="isFetchingTranscript" class="flex h-screen justify-center items-center">
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
    <div v-else class="relative flex flex-col p-20 w-full h-screen">
      <div class="flex-none">
        <!-- <div class="text-lg font-bold mb-4">关键字</div>
        <div class="text-lg font-bold mb-4">内容概要</div> -->
        <div class="text-lg font-bold mb-4">AI 转写结果</div>

        <!-- WaveSurfer Container -->
        <div class="relative group">
          <div v-if="isWaveformLoading" class="flex items-center justify-center h-[100px] bg-gray-100 dark:bg-gray-800 rounded-lg mb-4">
            <p class="text-gray-500 animate-pulse">正在加载音频波形...</p>
          </div>
          <div ref="waveform" class="mb-4"></div>
          <div v-if="!isWaveformLoading && audioUrl" class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
            <button @click="togglePlay" class="w-16 h-16 bg-black bg-opacity-50 rounded-full flex items-center justify-center text-white hover:bg-opacity-75 transition-all">
              <svg v-if="!isPlaying" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-8 h-8 ml-1">
                <path fill-rule="evenodd" d="M4.5 5.653c0-1.426 1.529-2.33 2.779-1.643l11.54 6.647c1.295.742 1.295 2.545 0 3.286L7.279 20.99c-1.25.72-2.779-.217-2.779-1.643V5.653z" clip-rule="evenodd" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-8 h-8">
                <path fill-rule="evenodd" d="M6.75 5.25a.75.75 0 01.75.75v12a.75.75 0 01-1.5 0v-12a.75.75 0 01.75-.75zM16.5 5.25a.75.75 0 01.75.75v12a.75.75 0 01-1.5 0v-12a.75.75 0 01.75-.75z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
        <div class="flex items-center justify-between gap-4 mb-4">
          <div class="text-sm font-mono">
            <span v-if="!isWaveformLoading && audioUrl">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
          </div>
          <button
            v-if="hasUnsavedChanges"
            @click="saveChanges"
            :disabled="isSaving"
            class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {{ isSaving ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </div>

      <!-- 如果有 segments，就分段显示 -->
      <div
        v-if="segments.length"
        ref="transcriptContainer"
        class="flex-grow p-4 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-white space-y-3 overflow-y-auto transition-opacity"
        :class="{ 'pointer-events-none opacity-50': isWaveformLoading }"
      >
        <div
          v-for="seg in segments"
          :key="seg.id"
          :ref="
            (el) => {
              if (seg && seg.id !== undefined) segmentRefs[seg.id] = el
            }
          "
          class="mb-2 p-2 rounded-md transition-colors duration-300"
          :class="{ 'bg-gray-100 dark:bg-gray-700': isSegmentActive(seg) }"
        >
          <p class="text-sm text-gray-500">
            [{{ formatTime(seg.start) }} - {{ formatTime(seg.end) }}]
          </p>
          <p class="leading-relaxed">
            <span
              v-for="(word, wordIndex) in seg.words"
              :key="wordIndex"
              @click="seekTo(word.start)"
              :class="{ 'bg-yellow-300 text-black rounded': isWordActive(word) }"
              class="cursor-pointer transition-colors duration-200"
              contenteditable="true"
              @blur="updateWord(seg.id, wordIndex, $event)"
            >
              {{ word.word }}
            </span>
          </p>
        </div>
      </div>

      <!-- 如果没 segments，就显示 text -->
      <div
        v-else
        class="flex-grow p-4 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-white whitespace-pre-line overflow-y-auto"
      >
        {{ text }}
      </div>
    </div>
  </div>
</template>

<script>
import WaveSurfer from 'wavesurfer.js'

export default {
  data() {
    return {
      text: '',
      segments: [],
      isFetchingTranscript: true,
      isWaveformLoading: false,
      error: null,
      loadingMessage: '',
      timer: null,
      audioUrl: null,
      currentTime: 0,
      duration: 0,
      activeSegmentId: null,
      segmentRefs: {},
      wavesurfer: null,
      isPlaying: false,
      hasUnsavedChanges: false,
      isSaving: false
    }
  },
  beforeUpdate() {
    this.segmentRefs = {}
  },
  methods: {
    updateWord(segmentId, wordIndex, event) {
      const newText = event.target.innerText.trim()
      const segment = this.segments.find((s) => s.id === segmentId)
      if (segment && segment.words[wordIndex].word !== newText) {
        segment.words[wordIndex].word = newText
        this.hasUnsavedChanges = true
      }
    },
    async saveChanges() {
      if (!this.hasUnsavedChanges) return
      this.isSaving = true
      try {
        const taskId = this.$route.params.task_id
        // 在保存前，根据修改后的 words 更新每个 segment 的 text 属性
        const updatedSegments = this.segments.map(seg => {
          const newText = seg.words.map(w => w.word).join(' ')
          return { ...seg, text: newText }
        })

        await this.$axios.post(`/api/stt-update`, {
          task_id: taskId,
          segments: updatedSegments
        })
        this.hasUnsavedChanges = false
        // 可以添加一个成功提示, 例如使用 Element Plus 的 ElMessage
        // this.$message.success('保存成功!')
      } catch (error) {
        console.error('保存失败:', error)
        // this.$message.error('保存失败，请稍后再试')
      } finally {
        this.isSaving = false
      }
    },
    async fetchTranscript(taskId) {
      this.isFetchingTranscript = true
      try {
        const response = await this.$axios.get(`/api/stt-progress/${taskId}`)
        if (response.data.code === 200) {
          this.clearTimer()
          const data = response.data.data
          this.text = data.text || ''
          this.segments = data.segments || []
          this.isFetchingTranscript = false // 关键：立即隐藏全局加载

          if (data.file_path) {
            this.isWaveformLoading = true // 显示波形图加载
            const baseUrl = import.meta.env.VITE_BASE_URL
            this.audioUrl = `${baseUrl}/${data.file_path}`
            this.$nextTick(() => {
              this.initWaveSurfer()
            })
          }
        } else if (response.data.code === 100001) {
          this.loadingMessage = '音视频文件转写中，请稍等...'
          this.clearTimer()
          this.timer = setTimeout(() => {
            this.fetchTranscript(taskId)
          }, 3000)
        } else {
          throw new Error(`错误: ${response.data.message}`)
        }
      } catch (err) {
        this.error = err.message || '获取转写文本时出现错误'
        this.isFetchingTranscript = false
        this.clearTimer()
      }
    },
    initWaveSurfer() {
      if (!this.$refs.waveform) return
      this.wavesurfer = WaveSurfer.create({
        container: this.$refs.waveform,
        waveColor: '#A78BFA',
        progressColor: '#8B5CF6',
        url: this.audioUrl,
        // barWidth: 3,
        // barRadius: 3,
        // barGap: 2,
        // height: 100
      })

      this.wavesurfer.on('ready', (duration) => {
        this.duration = duration
        this.isWaveformLoading = false // 关键：隐藏波形图加载
      })

      this.wavesurfer.on('audioprocess', (currentTime) => {
        this.onTimeUpdate(currentTime)
      })

      this.wavesurfer.on('play', () => {
        this.isPlaying = true
      })

      this.wavesurfer.on('pause', () => {
        this.isPlaying = false
      })

      this.wavesurfer.on('finish', () => {
        this.isPlaying = false
      })
    },
    togglePlay() {
      if (this.wavesurfer) {
        this.wavesurfer.playPause()
      }
    },
    clearTimer() {
      if (this.timer) {
        clearTimeout(this.timer)
        this.timer = null
      }
    },
    formatTime(sec) {
      if (isNaN(sec)) return '00:00.000'
      const minutes = Math.floor(sec / 60)
      const seconds = Math.floor(sec % 60)
      const milliseconds = Math.round((sec - Math.floor(sec)) * 1000)
      return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${milliseconds.toString().padStart(3, '0')}`
    },
    onTimeUpdate(currentTime) {
      this.currentTime = currentTime
      const activeSegment = this.segments.find(
        (seg) => this.currentTime >= seg.start && this.currentTime < seg.end
      )

      if (activeSegment && activeSegment.id !== this.activeSegmentId) {
        this.activeSegmentId = activeSegment.id
        this.scrollToActiveSegment()
      } else if (!activeSegment && this.activeSegmentId !== null) {
        this.activeSegmentId = null
      }
    },
    scrollToActiveSegment() {
      this.$nextTick(() => {
        const activeEl = this.segmentRefs[this.activeSegmentId]
        if (activeEl) {
          activeEl.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
          })
        }
      })
    },
    isSegmentActive(segment) {
      if (!segment) return false
      return this.currentTime >= segment.start && this.currentTime < segment.end
    },
    isWordActive(word) {
      if (!word || typeof word.start === 'undefined' || typeof word.end === 'undefined') {
        return false
      }
      return this.currentTime >= word.start && this.currentTime < word.end
    },
    seekTo(time) {
      if (this.wavesurfer && typeof time === 'number') {
        this.wavesurfer.setTime(time)
        this.wavesurfer.play()
      }
    }
  },
  beforeUnmount() {
    if (this.wavesurfer) {
      this.wavesurfer.destroy()
    }
    document.body.style.overflowY = ''
    this.clearTimer()
  },
  mounted() {
    document.body.style.overflowY = 'hidden'
    const taskId = this.$route.params.task_id
    if (taskId) {
      this.loadingMessage = '正在获取转写结果，请稍候...'
      this.fetchTranscript(taskId)
    } else {
      this.error = '没有提供任务ID'
      this.isFetchingTranscript = false
    }
  }
}
</script>
