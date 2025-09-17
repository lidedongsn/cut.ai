<template>
  <div class="bg-white dark:bg-gray-900 text-gray-800 dark:text-white h-full flex flex-col">
    <!-- 全局加载状态 -->
    <div v-if="isFetchingTranscript" class="flex-grow flex justify-center items-center">
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
    <div v-else :class="['flex-grow p-4 sm:p-8 grid gap-8 overflow-hidden', isVideo ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1']">
      <!-- Left Column: Media Player -->
      <div class="flex flex-col overflow-y-auto">
        <div class="text-2xl font-bold mb-4 flex-shrink-0">AI 转写结果</div>
        <!-- Video Player -->
        <video
          v-if="isVideo"
          ref="videoPlayer"
          :src="audioUrl"
          class="w-full rounded-lg mb-4 bg-black aspect-video flex-shrink-0"
          muted
          playsinline
        ></video>

        <!-- WaveSurfer Container -->
        <div class="relative group flex-shrink-0">
          <div v-if="isWaveformLoading" class="flex items-center justify-center h-[100px] bg-gray-100 dark:bg-gray-800 rounded-lg mb-4">
            <p class="text-gray-500 animate-pulse">正在加载音频波形...</p>
          </div>
          <div ref="waveform" class="mb-4"></div>
          <div v-if="!isWaveformLoading && audioUrl" class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
            <button @click="togglePlay" class="w-20 h-20 rounded-full flex items-center justify-center text-gray-700 dark:text-gray-300 hover:ring-2 hover:ring-gray-500/50 transition-all group">
              <svg v-if="!isPlaying" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-12 h-12 ml-1 opacity-75 group-hover:opacity-100 transition-opacity" style="filter: drop-shadow(0 1px 2px rgb(0 0 0 / 0.5));">
                <path fill-rule="evenodd" d="M4.5 5.653c0-1.426 1.529-2.33 2.779-1.643l11.54 6.647c1.295.742 1.295 2.545 0 3.286L7.279 20.99c-1.25.72-2.779-.217-2.779-1.643V5.653z" clip-rule="evenodd" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-12 h-12 opacity-75 group-hover:opacity-100 transition-opacity" style="filter: drop-shadow(0 1px 2px rgb(0 0 0 / 0.5));">
                <path fill-rule="evenodd" d="M6.75 5.25a.75.75 0 01.75.75v12a.75.75 0 01-1.5 0v-12a.75.75 0 01.75-.75zM16.5 5.25a.75.75 0 01.75.75v12a.75.75 0 01-1.5 0v-12a.75.75 0 01.75-.75z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
        <div v-if="!isWaveformLoading && audioUrl" class="text-center mb-4 flex-shrink-0">
          <div class="text-sm font-mono">
            {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
          </div>
        </div>
      </div>

      <!-- Right Column: Transcript -->
      <div class="flex flex-col h-full overflow-hidden">
        <div class="flex justify-between items-center mb-4 flex-shrink-0">
           <h2 class="text-2xl font-bold">转写文本</h2>
           <button
              v-if="hasUnsavedChanges"
              @click="saveChanges"
              :disabled="isSaving"
              class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {{ isSaving ? '保存中...' : '保存修改' }}
            </button>
        </div>
        <div
          v-if="segments.length"
          ref="transcriptContainer"
          class="flex-grow p-4 rounded-lg bg-gray-50 dark:bg-gray-800 space-y-3 overflow-y-auto transition-opacity"
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
            :class="{ 'bg-gray-200 dark:bg-gray-700': isSegmentActive(seg) }"
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
        <!-- Fallback for plain text -->
        <div v-else class="flex-grow p-4 rounded-lg bg-gray-50 dark:bg-gray-800 whitespace-pre-line overflow-y-auto">
          {{ text }}
        </div>
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
      fileType: null,
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
  computed: {
    isVideo() {
      return this.fileType && this.fileType.startsWith('video/');
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
        const updatedSegments = this.segments.map(seg => {
          const newText = seg.words.map(w => w.word).join(' ')
          return { ...seg, text: newText }
        })

        await this.$axios.post(`/api/stt-update`, {
          task_id: taskId,
          segments: updatedSegments
        })
        this.hasUnsavedChanges = false
      } catch (error) {
        console.error('保存失败:', error)
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
          this.fileType = data.file_type || ''
          this.isFetchingTranscript = false

          if (data.file_path) {
            this.isWaveformLoading = true
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
      })

      this.wavesurfer.on('ready', (duration) => {
        this.duration = duration
        this.isWaveformLoading = false
      })

      this.wavesurfer.on('audioprocess', (currentTime) => {
        this.onTimeUpdate(currentTime)
      })

      this.wavesurfer.on('play', () => {
        this.isPlaying = true
        if (this.isVideo) this.$refs.videoPlayer.play()
      })

      this.wavesurfer.on('pause', () => {
        this.isPlaying = false
        if (this.isVideo) this.$refs.videoPlayer.pause()
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
      // Force sync video with audio
      if (this.isVideo && this.$refs.videoPlayer) {
        const timeDiff = Math.abs(this.$refs.videoPlayer.currentTime - currentTime)
        if (timeDiff > 0.2) { // Sync if discrepancy is larger than 200ms
          this.$refs.videoPlayer.currentTime = currentTime
        }
      }
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
        // Also seek the video
        if (this.isVideo && this.$refs.videoPlayer) {
          this.$refs.videoPlayer.currentTime = time
        }
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
