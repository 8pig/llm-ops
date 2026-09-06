<script setup lang="ts">
import Banner from './components/LoginBanner.vue'
import LoginForm from './components/LoginForm.vue'
</script>

<template>
  <!-- 页面容器 -->
  <div class="flex h-screen bg-[#f5f7fb]">
    <!-- 左侧律所主题banner -->
    <banner />
    <!-- 右侧表单 -->
    <div class="relative flex flex-1 items-center justify-center pb-16">
      <!-- 登录表单 -->
      <login-form />
      <!-- 底部footer -->
      <div class="absolute right-0 bottom-0 w-full">
        <footer class="flex items-center justify-center h-10 text-gray-400 text-center text-xs">
          坤盛AI辅助平台 · 让 AI 成为律师的超级副手
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
