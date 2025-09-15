<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="relative h-screen bg-white dark:bg-gray-900 text-gray-800 dark:text-white">
    <header class="absolute top-8 left-10 z-20">
      <RouterLink to="/" class="flex items-center space-x-1 w-fit">
        <span class="text-pink-500 font-bold text-3xl">CUT</span>
        <span class="text-purple-500 font-medium text-3xl">AI™</span>
      </RouterLink>
    </header>
    <main class="h-full" :class="{ 'pt-24 px-4 sm:px-8': $route.meta.layout !== 'centered' }">
      <RouterView />
    </main>
  </div>
</template>

<style>
/* CUSTOM STYLE */
</style>
