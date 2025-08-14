<template>
  <div class="flex justify-center items-center h-screen bg-white dark:bg-gray-900 text-gray-800 dark:text-white ">
    <FileUpload />
  </div>
</template>

<script>
import FileUpload from '@/components/FileUpload.vue'
export default {
  components: {
    FileUpload
  },
}
</script>

<style>
/* 可以在这里添加 CSS 样式 */
</style>
