import { onMounted, reactive, ref } from 'vue'
import {
  cancelPublish,
  debugChat,
  deleteDebugConversation,
  fallbackHistoryToDraft,
  getApp,
  getDebugConversationMessagesWithPage,
  getDebugConversationSummary,
  getDraftAppConfig,
  getPublishHistoriesWithPage,
  publish,
  stopDebugChat,
  updateDebugConversationSummary,
  updateDraftAppConfig,
} from '@/services/app'
import { Message, Modal } from '@arco-design/web-vue'
import type {
  GetDebugConversationMessagesWithPageResponse,
  UpdateDraftAppConfigRequest,
} from '@/models/app'

export const useGetApp = (app_id: string) => {
  // 1.定义hooks所需的基础数据
  const loading = ref(false)
  const app = reactive<Record<string, any>>({})

  // 2.定义加载数据所需的函数
  const loadApp = async (app_id: string) => {
    try {
      loading.value = true
      const resp = await getApp(app_id)
      const data = resp.data

      Object.assign(app, { ...data })
    } finally {
      loading.value = false
    }
  }

  // 3.页面DOM加载完毕时加载一次数据
  onMounted(async () => await loadApp(app_id))

  return { loading, app, loadApp }
}

export const usePublish = () => {
  // 1.定义hooks所需的数据
  const loading = ref(false)

  // 2.定义更新发布处理器
  const handlePublish = async (app_id: string) => {
    try {
      loading.value = true
      const resp = await publish(app_id)
      Message.success(resp.message)
    } finally {
      loading.value = false
    }
  }

  return { loading, handlePublish }
}

export const useCancelPublish = () => {
  // 1.定义hooks所需的数据
  const loading = ref(false)

  // 2.定义取消发布处理器
  const handleCancelPublish = async (app_id: string, callback?: () => void) => {
    // 2.1打开弹窗提示
    Modal.warning({
      title: '要取消发布该Agent应用吗?',
      content:
        '取消发布后，WebApp以及发布的社交平台均无法使用该Agent，如需更新WebApp地址，请使用地址重新生成功能',
      hideCancel: false,
      onOk: async () => {
        try {
          // 2.2 点击确定后向API接口发起请求
          loading.value = true
          const resp = await cancelPublish(app_id)
          Message.success(resp.message)
        } finally {
          // 2.3 调用callback函数指定回调功能
          loading.value = false
          callback && callback()
        }
      },
    })
  }

  return { loading, handleCancelPublish }
}

export const useGetPublishHistoriesWithPage = () => {
  // 1.定义hooks所需的数据
  const loading = ref(false)
  const defaultPaginator = {
    current_page: 1,
    page_size: 20,
    total_page: 0,
    total_record: 0,
  }
  const publishHistories = reactive<Array<Record<string, any>>>([])
  const paginator = reactive({ ...defaultPaginator })

  // 2.定义加载数据函数
  const loadPublishHistories = async (app_id: string, init: boolean = false) => {
    try {
      // 2.1 判断是否为初始化，如果是则先初始化分页器
      if (init) {
        Object.assign(paginator, { ...defaultPaginator })
      } else if (paginator.current_page > paginator.total_page) {
        return
      }

      // 2.2 调用API接口获取数据
      loading.value = true
      const resp = await getPublishHistoriesWithPage(app_id, {
        current_page: paginator.current_page,
        page_size: paginator.page_size,
      })
      const data = resp.data

      // 2.3 更新分页器数据
      paginator.current_page = data.paginator.current_page
      paginator.page_size = data.paginator.page_size
      paginator.total_page = data.paginator.total_page
      paginator.total_record = data.paginator.total_record

      // 2.4 是否存在更多数据
      if (paginator.current_page <= paginator.total_page) {
        paginator.current_page += 1
      }

      // 2.5 检测是追加数据还是覆盖数据
      if (init) {
        publishHistories.splice(0, publishHistories.length, ...data.list)
      } else {
        publishHistories.push(...data.list)
      }
    } finally {
      loading.value = false
    }
  }

  return { loading, publishHistories, paginator, loadPublishHistories }
}

export const useFallbackHistoryToDraft = () => {
  // 1.定义hooks所需的数据
  const loading = ref(false)

  // 2.定义回退处理器
  const handleFallbackHistoryToDraft = async (
    app_id: string,
    app_config_version_id: string,
    callback?: () => void,
  ) => {
    try {
      loading.value = true
      const resp = await fallbackHistoryToDraft(app_id, app_config_version_id)
      Message.success(resp.message)
    } finally {
      loading.value = false
      callback && callback()
    }
  }

  return { loading, handleFallbackHistoryToDraft }
}

export const useGetDraftAppConfig = (app_id: string) => {
  // 1.定义hooks所需数据
  const loading = ref(false)
  const draftAppConfigForm = reactive<Record<string, any>>({})

  // 2.定义加载数据函数
  const loadDraftAppConfig = async (app_id: string) => {
    try {
      // 2.1 修改loading状态并获取数据
      loading.value = true
      const resp = await getDraftAppConfig(app_id)
      const data = resp.data

      // 2.2 将数据同步到表单中
      Object.assign(draftAppConfigForm, {
        preset_prompt: data.preset_prompt,
        long_term_memory: data.long_term_memory,
        opening_statement: data.opening_statement,
        opening_questions: data.opening_questions,
        suggested_after_answer: data.suggested_after_answer,
        review_config: data.review_config,
        datasets: data.datasets,
        retrieval_config: data.retrieval_config,
        tools: data.tools,
      })
    } finally {
      loading.value = false
    }
  }

  onMounted(async () => await loadDraftAppConfig(app_id))

  return { loading, draftAppConfigForm, loadDraftAppConfig }
}

export const useUpdateDraftAppConfig = () => {
  // 1.定义hooks所需数据
  const loading = ref(false)

  // 2.定义更新草稿配置处理器
  const handleUpdateDraftAppConfig = async (
    app_id: string,
    draft_app_config: UpdateDraftAppConfigRequest,
  ) => {
    try {
      loading.value = true
      const resp = await updateDraftAppConfig(app_id, draft_app_config)
      Message.success(resp.message)
    } finally {
      loading.value = false
    }
  }

  return { loading, handleUpdateDraftAppConfig }
}

export const useGetDebugConversationSummary = () => {
  // 1.定义hooks所需数据
  const loading = ref(false)
  const debug_conversation_summary = ref('')

  // 2.定义数据加载函数
  const loadDebugConversationSummary = async (app_id: string) => {
    try {
      // 2.1 调用API获取记忆
      loading.value = true
      const resp = await getDebugConversationSummary(app_id)
      const data = resp.data

      debug_conversation_summary.value = data.summary
    } finally {
      loading.value = false
    }
  }

  return { loading, debug_conversation_summary, loadDebugConversationSummary }
}

export const useUpdateDebugConversationSummary = () => {
  // 1.定义hooks所需数据
  const loading = ref(false)

  // 2.定义更新处理器
  const handleUpdateDebugConversationSummary = async (app_id: string, summary: string) => {
    try {
      loading.value = true
      const resp = await updateDebugConversationSummary(app_id, summary)
      Message.success(resp.message)
    } finally {
      loading.value = false
    }
  }

  return { loading, handleUpdateDebugConversationSummary }
}

export const useDeleteDebugConversation = () => {
  // 1.定义hooks所需数据
  const loading = ref(false)

  // 2.定义删除调试会话处理器
  const handleDeleteDebugConversation = async (app_id: string) => {
    try {
      loading.value = true
      const resp = await deleteDebugConversation(app_id)
      Message.success(resp.message)
    } finally {
      loading.value = false
    }
  }

  return { loading, handleDeleteDebugConversation }
}

export const useGetDebugConversationMessagesWithPage = () => {
  // 1.定义hooks所需数据
  const loading = ref(false)
  const messages = ref<GetDebugConversationMessagesWithPageResponse['data']['list']>([])
  const created_at = ref(0)
  const defaultPaginator = {
    current_page: 1,
    page_size: 5,
    total_page: 0,
    total_record: 0,
  }
  const paginator = ref({ ...defaultPaginator })

  // 2.定义加载数据函数
  const loadDebugConversationMessages = async (app_id: string, init: boolean = false) => {
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
      const resp = await getDebugConversationMessagesWithPage(app_id, {
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

  return { loading, messages, paginator, loadDebugConversationMessages }
}

export const useDebugChat = () => {
  // 1.定义hooks所需数据
  const loading = ref(false)

  // 2.定义调试会话处理器
  const handleDebugChat = async (
    app_id: string,
    query: string,
    onData: (event_response: Record<string, any>) => void,
  ) => {
    try {
      loading.value = true
      await debugChat(app_id, query, onData)
    } finally {
      loading.value = false
    }
  }

  return { loading, handleDebugChat }
}

export const useStopDebugChat = () => {
  // 1.定义hooks所需数据
  const loading = ref(false)

  // 2.定义停止调试会话处理器
  const handleStopDebugChat = async (app_id: string, task_id: string) => {
    try {
      loading.value = true
      await stopDebugChat(app_id, task_id)
    } finally {
      loading.value = false
    }
  }

  return { loading, handleStopDebugChat }
}
