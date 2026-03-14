<script setup lang="ts">
import { post } from '@/utils/request.ts';

const debug = async () => {
  const resp = await post('/apps/550e8400-e29b-41d4-a716-446655440000/debug', {
    body: {
      query: '你是谁',
    },
  });
  console.log(resp);
};
</script>

<template>
  <a-button @click="debug">发起请求</a-button>
</template>

<style scoped></style>
