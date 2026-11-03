import { onUnmounted, ref } from 'vue'
import {
  assistantAgentChat,
  deleteAssistantAgentConversation,
  getAssistantAgentMessagesWithPage,
  stopAssistantAgentChat,
} from '@/services/assistant-agent'
import type { GetAssistantAgentMessagesWithPageResponse } from '@/models/assistant-agent'
import { Message } from '@arco-design/web-vue'

export const useAssistantAgentChat = () => {
  // 1.定义自定义hooks所需数据
  const loading = ref(false)

  // 2.记录当前进行中的流式请求
  //  SSE响应带Connection: close，不主动中断会一直占用浏览器对同一host的并发槽位，
  //  占满(HTTP/1.1为6条)后新请求会一直卡在Stalled状态
  let controller: AbortController | null = null

  // 3.中断当前正在进行的流式请求并释放连接
  const abortAssistantAgentChat = () => {
    controller?.abort()
    controller = null
  }

  // 4.定义辅助Agent会话处理器
  const handleAssistantAgentChat = async (
    query: string,
    image_urls: string[] =[],
    onData: (event_response: Record<string, any>) => void,
  ) => {
    // 4.1 发起新请求前先结束上一条，避免连接堆积
    abortAssistantAgentChat()
    const current = new AbortController()
    controller = current

    try {
      loading.value = true
      await assistantAgentChat(query, image_urls, onData, current.signal)
    } catch (e) {
      // 4.2 主动取消属于预期行为，不向上抛出
      if ((e as Error)?.name !== 'AbortError') throw e
    } finally {
      // 4.3 仅当自己仍是当前请求时才复位状态，避免影响后续新请求
      if (controller === current) {
        controller = null
        loading.value = false
      }
    }
  }

  // 5.组件卸载时释放连接
  onUnmounted(abortAssistantAgentChat)

  return { loading, handleAssistantAgentChat, abortAssistantAgentChat }
}

export const useStopAssistantAgentChat = () => {
  // 1.定义hooks所需数据
  const loading = ref(false)

  // 2.定义停止辅助Agent会话处理器
  const handleStopAssistantAgentChat = async (task_id: string) => {
    try {
      loading.value = true
      await stopAssistantAgentChat(task_id)
    } finally {
      loading.value = false
    }
  }

  return { loading, handleStopAssistantAgentChat }
}

export const useGetAssistantAgentMessagesWithPage = () => {
  // 1.定义hooks所需数据
  const loading = ref(false)
  const messages = ref<GetAssistantAgentMessagesWithPageResponse['data']['list']>([])
  const created_at = ref(0)
  const defaultPaginator = {
    current_page: 1,
    page_size: 5,
    total_page: 0,
    total_record: 0,
  }
  const paginator = ref({ ...defaultPaginator })

  // 2.定义加载数据函数
  const loadAssistantAgentMessages = async (init: boolean = false) => {
    // 2.1 判断是否是初始化，如果是则先初始化分页器
    if (init) {
      paginator.value = { ...defaultPaginator }
      created_at.value = 0
    } else if (paginator.value.current_page > paginator.value.total_page) {
      return
    }

    // 2.2 加载更多数据
    try {
      loading.value = true
      const resp = await getAssistantAgentMessagesWithPage({
        current_page: paginator.value.current_page,
        page_size: paginator.value.page_size,
        created_at: created_at.value,
      })
      const data = resp.data

      // 2.3 更新分页器
      paginator.value = data.paginator

      // 2.4 判断是否存在更多数据
      if (paginator.value.current_page <= paginator.value.total_page) {
        paginator.value.current_page += 1
      }

      // 2.5 追加或者覆盖数据
      if (init) {
        messages.value = data.list
      } else {
        messages.value.push(...data.list)
        created_at.value = data.list[0]?.created_at ?? 0
      }
    } finally {
      loading.value = false
    }
  }

  return { loading, messages, paginator, loadAssistantAgentMessages }
}

export const useDeleteAssistantAgentConversation = () => {
  // 1.定义hooks所需数据
  const loading = ref(false)

  // 2.定义删除调试会话处理器
  const handleDeleteAssistantAgentConversation = async () => {
    try {
      loading.value = true
      const resp = await deleteAssistantAgentConversation()
      Message.success(resp.message)
    } finally {
      loading.value = false
    }
  }

  return { loading, handleDeleteAssistantAgentConversation }
}
