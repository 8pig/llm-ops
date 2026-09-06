<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCredentialStore } from '@/stores/credential'
import { Message, type ValidatedError } from '@arco-design/web-vue'
import { provider } from '@/services/oauth'
import { passwordLogin } from '@/services/auth'

// 1.定义自定义组件所需数据
const errorMessage = ref('')
const passwordLoading = ref(false)
const githubLoading = ref(false)
const loginForm = reactive({ email: '', password: '' })
const credentialStore = useCredentialStore()
const router = useRouter()

// 2.定义忘记密码点击事件
const forgetPassword = () => Message.error('忘记密码请联系管理员')

// 3.定义github第三方授权认证登录
const githubLogin = async () => {
  try {
    githubLoading.value = true
    const resp = await provider('github')
    window.location.href = resp.data.redirect_url
  } finally {
    githubLoading.value = false
  }
}

// 4.账号密码登录
const handleSubmit = async ({ errors }: { errors: Record<string, ValidatedError> | undefined }) => {
  // 4.1 判断表单是否校验成功
  if (errors) return

  // 4.2 如果没有出错则发起请求进行登录
  try {
    // 4.3 发起账号密码登录，并且将loading设置为true
    passwordLoading.value = true
    const resp = await passwordLogin(loginForm.email, loginForm.password)
    Message.success('登录成功，正在跳转')
    credentialStore.update(resp.data)
    await router.replace({ path: '/home' })
  } catch (error: any) {
    // 4.4 添加错误信息并清除密码
    errorMessage.value = error.message
    loginForm.password = ''
  } finally {
    passwordLoading.value = false
  }
}
</script>

<template>
  <div class="w-[380px]">
    <!-- 顶部品牌 -->
    <div class="flex items-center gap-3">
      <div
        class="w-11 h-11 rounded-xl flex items-center justify-center shadow-sm"
        style="background: linear-gradient(135deg, #0a1740 0%, #1e40af 100%)"
      >
        <svg viewBox="0 0 24 24" class="w-6 h-6" fill="none" aria-hidden="true">
          <path
            d="M12 3v18M12 3l-2.2 2.4M12 3l2.2 2.4M12 6.2v0M6.5 12.5h11M6.5 12.5a2.2 2.2 0 1 0-2.2 2.2M17.5 12.5a2.2 2.2 0 1 1-2.2 2.2"
            stroke="#e5cf96"
            stroke-width="1.5"
            stroke-linecap="round"
          />
        </svg>
      </div>
      <div class="flex flex-col leading-tight">
        <div class="text-gray-900 font-bold text-xl leading-7">坤盛AI辅助平台</div>
        <p class="text-xs leading-5 text-gray-400 tracking-wide">
          法律科技赋能 · 让团队专注专业价值
        </p>
      </div>
    </div>
    <!-- 登录说明 -->
    <div class="mt-7 mb-1">
      <div class="text-gray-900 font-semibold text-lg">欢迎回来</div>
      <p class="text-sm text-gray-500 mt-0.5">请使用机构分配的账号登录系统</p>
    </div>
    <!-- 错误提示占位符 -->
    <div class="h-8 text-red-700 leading-8 line-clamp-1">{{ errorMessage }}</div>
    <!-- 登录表单 -->
    <a-form
      :model="loginForm"
      @submit="handleSubmit"
      layout="vertical"
      size="large"
      class="flex flex-col w-full"
    >
      <a-form-item
        field="email"
        :rules="[{ type: 'email', required: true, message: '登录账号必须是合法的邮箱' }]"
        :validate-trigger="['change', 'blur']"
        hide-label
      >
        <a-input v-model="loginForm.email" size="large" placeholder="登录账号（邮箱）">
          <template #prefix>
            <icon-user />
          </template>
        </a-input>
      </a-form-item>
      <a-form-item
        field="password"
        :rules="[{ required: true, message: '账号密码不能为空' }]"
        :validate-trigger="['change', 'blur']"
        hide-label
      >
        <a-input-password v-model="loginForm.password" size="large" placeholder="账号密码">
          <template #prefix>
            <icon-lock />
          </template>
        </a-input-password>
      </a-form-item>
      <a-space :size="16" direction="vertical">
        <div class="flex justify-between">
          <a-checkbox>记住密码</a-checkbox>
          <a-link @click="forgetPassword">忘记密码?</a-link>
        </div>
        <a-button :loading="passwordLoading" size="large" type="primary" html-type="submit" long>
          登 录
        </a-button>
        <a-button :loading="githubLoading" size="large" type="text" long @click="githubLogin">
          <template #icon>
            <icon-github />
          </template>
          使用 GitHub 账号登录
        </a-button>
      </a-space>
    </a-form>
  </div>
</template>

<style scoped></style>
