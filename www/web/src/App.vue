<script setup>
import { RouterView } from 'vue-router'
</script>

<template>
   <div class="absolute top-8 left-10 flex items-center space-x-1">
      <!-- 图标 -->
      <!-- <img src="@/assets/logo.png" alt="CUT AI" class="w-10 h-10" /> -->
      <!-- 文字 -->
      <span class="text-pink-500 font-bold text-3xl">CUT</span>
      <span class="text-purple-500 font-medium text-3xl">AI™</span>
    </div>
  <RouterView />
</template>

<style>
/* CUSTOM STYLE */
</style>
