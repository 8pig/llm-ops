<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Forbidden from '@/assets/images/forbidden.png'

const route = useRoute()
// 从 request.ts 跳转时携带的失败原因，便于用户定位问题（非权限类错误也会走这里）
const reason = computed(() => String(route.query?.reason ?? ''))
</script>

<template>
  <div class="h-full flex flex-col items-center justify-center">
    <!-- 页面背景 -->
    <img :src="Forbidden" alt="NotFound" class="w-[300px] mb-6" />
    <div class="text-base text-gray-700 font-semibold mb-3">对不起，您暂无权限访问该页面！</div>
    <div class="text-gray-500 mb-6">
      <div v-if="reason" class="">· {{ reason }}</div>
      <div v-else class="">· 您可能没有访问该页面的权限</div>
      <div class="">· 页面可能已被禁用或不存在</div>
    </div>
    <router-link :to="{ name: 'pages-home' }">
      <a-button type="primary">前往首页</a-button>
    </router-link>
  </div>
</template>

<style scoped></style>
