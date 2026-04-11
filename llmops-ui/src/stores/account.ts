import { defineStore } from 'pinia'
import { ref } from 'vue'

// 初始值
const initAccount = {
  name: '慕小课',
  email: 'imooc@163.com',
  avatar: '',
}

export const useAccountStore = defineStore('account', () => {
  // 1.定义数据
  const account = ref({ ...initAccount })

  // 2.函数/动作
  function update(params: any) {
    Object.assign(account.value, params)
  }

  function clear() {
    account.value = { ...initAccount }
  }

  return { account, update, clear }
})
