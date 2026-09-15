<script setup lang="ts">
// @ts-ignore
import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
import { onMounted, onUnmounted, type PropType, ref } from 'vue'
import { useRoute } from 'vue-router'
import AudioRecorder from 'js-audio-recorder'
import {
  useDebugChat,
  useDeleteDebugConversation,
  useGetDebugConversationMessagesWithPage,
  useStopDebugChat,
} from '@/hooks/use-app'
import { useAudioPlayer, useAudioToText } from '@/hooks/use-audio'
import { useGenerateSuggestedQuestions } from '@/hooks/use-ai'
import { useScrollToBottomUntilStable } from '@/hooks/use-auto-scroll'
import { useAccountStore } from '@/stores/account'
import HumanMessage from '@/components/HumanMessage.vue'
import AiMessage from '@/components/AiMessage.vue'
import { Message } from '@arco-design/web-vue'
import { QueueEvent } from '@/config'
import { uploadImage } from '@/services/upload-file'

// 1.定义自定义组件所需数据
const route = useRoute()
const props = defineProps({
  app: { type: Object, default: {}, required: true },
  suggested_after_answer: {
    type: Object as PropType<{ enable: boolean }>,
    default: { enable: true },
    required: true,
  },
  opening_statement: { type: String, default: '', required: true },
  opening_questions: { type: Array as PropType<string[]>, default: [], required: true },
  text_to_speech: {
    type: Object,
    default: () => {
      return {
        enable: false,
        auto_play: false,
        voice: 'echo',
      }
    },
    required: false,
  },
})
const query = ref('')
const message_id = ref('')
const active_message_id = ref('')
const image_urls = ref<string[]>([])
const fileInput = ref<any>(null)
const uploadFileLoading = ref(false)
const isRecording = ref(false) // 是否正在录音
const audioBlob = ref<any>(null) // 录音后音频的blob
let recorder: any = null // RecordRTC实例
const task_id = ref('')
const scroller = ref<any>(null)
const scrollHeight = ref(0)
const accountStore = useAccountStore()
const { loading: deleteDebugConversationLoading, handleDeleteDebugConversation } =
  useDeleteDebugConversation()
const {
  loading: getDebugConversationMessagesWithPageLoading,
  messages,
  paginator,
  loadDebugConversationMessages,
} = useGetDebugConversationMessagesWithPage()
const { loading: debugChatLoading, handleDebugChat } = useDebugChat()
const { loading: stopDebugChatLoading, handleStopDebugChat } = useStopDebugChat()
const { loading: suggestedQuestionsLoading, suggested_questions, handleGenerateSuggestedQuestions } =
  useGenerateSuggestedQuestions()
const { loading: audioToTextLoading, text, handleAudioToText } = useAudioToText()
const { startAudioStream, stopAudioStream } = useAudioPlayer()
const { createPendingId, scrollToBottom, scrollToBottomUntilStable } =
  useScrollToBottomUntilStable(scroller)

// 2.定义保存滚动高度函数
const saveScrollHeight = () => {
  scrollHeight.value = scroller.value.$el.scrollHeight
}

// 3.定义还原滚动高度函数
const restoreScrollPosition = () => {
  scroller.value.$el.scrollTop = scroller.value.$el.scrollHeight - scrollHeight.value
}

// 4.定义滚动函数
const handleScroll = async (event: UIEvent) => {
  const { scrollTop } = event.target as HTMLElement
  if (scrollTop <= 0 && !getDebugConversationMessagesWithPageLoading.value) {
    saveScrollHeight()
    await loadDebugConversationMessages(String(route.params?.app_id), false)
    restoreScrollPosition()
  }
}

// 5.定义输入框提交函数
const handleSubmit = async () => {
  // 5.1 检测是否录入了query，如果没有则结束
  if (query.value.trim() === '') {
    Message.warning('用户提问不能为空')
    return
  }

  // 5.2 检测上次提问是否结束，如果没结束不能发起新提问
  if (debugChatLoading.value) {
    Message.warning('上一次提问还未结束，请稍等')
    return
  }

  // 5.3 满足条件，处理正式提问的前置工作，涵盖：清空建议问题、删除消息id、任务id
  suggested_questions.value = []
  message_id.value = ''
  task_id.value = ''
  stopAudioStream()
  // 5.4 往消息列表中添加基础人类消息，id使用临时值避免虚拟滚动key冲突
  const pending_id = createPendingId()
  active_message_id.value = pending_id
  messages.value.unshift({
    id: pending_id,
    conversation_id: '',
    query: query.value,
    answer: '',
    image_urls: image_urls.value,
    total_token_count: 0,
    latency: 0,
    agent_thoughts: [],
    created_at: 0,
  })

  // 5.5 等待新消息渲染后滚动到底部，避免发送后视口停在原位
  await scrollToBottomUntilStable()

  // 5.6 初始化推理过程数据，并清空输入数据
  let position = 0
  const humanQuery = query.value
  const humanImageUrls = image_urls.value
  query.value = ''
  image_urls.value = []

  // 5.7 调用hooks发起请求
  await handleDebugChat(props.app?.id, humanQuery, humanImageUrls, (event_response) => {
    console.log(JSON.stringify(event_response, null, 2))
    // 5.7 提取流式事件响应数据以及事件名称
    const event = event_response?.event
    const data = event_response?.data
    const event_id = data?.id
    const event_name = data?.event

    // 5.8 初始化数据检测与赋值
    if (message_id.value === '' && data?.message_id) {
      task_id.value = data?.task_id
      message_id.value = data?.message_id
      active_message_id.value = data?.message_id
      messages.value[0].id = data?.message_id
      messages.value[0].conversation_id = data?.conversation_id
    }

    // 5.9 循环处理得到的事件，记录除ping之外的事件
    if (event_name !== QueueEvent.ping) {
      // 每次都从 messages.value[0] 获取最新的 agent_thoughts
      const agent_thoughts = messages.value[0].agent_thoughts

      // 5.10 处理agent_message事件，相同id的消息进行累加
      if (event_name === QueueEvent.agentMessage) {
        // 5.11 获取数据索引并检测是否存在
        const agent_thought_idx = agent_thoughts.findIndex((item: any) => item?.id === event_id)
        console.log(
          'event_id:',
          event_id,
          'findIndex:',
          agent_thought_idx,
          'total:',
          agent_thoughts.length,
        )

        // 5.12 数据不存在则添加新记录
        if (agent_thought_idx === -1) {
          position += 1
          agent_thoughts.push({
            id: event_id,
            position: position,
            event: event_name,
            thought: data?.thought || '',
            observation: data?.observation || '',
            tool: data?.tool || '',
            tool_input: data?.tool_input || {},
            latency: data?.latency || 0,
            created_at: 0,
          })
        } else {
          // 5.13 数据已存在，累加thought和observation内容
          const existingItem = agent_thoughts[agent_thought_idx]
          agent_thoughts[agent_thought_idx] = {
            ...existingItem,
            thought: (existingItem.thought || '') + (data?.thought || ''),
            observation: (existingItem.observation || '') + (data?.observation || ''),
            latency: data?.latency || existingItem.latency,
          }
        }

        // 5.14 累加answer答案（用于聊天区域显示）
        messages.value[0].answer = (messages.value[0].answer || '') + (data?.thought || '')
        messages.value[0].latency = data?.latency || ''
        messages.value[0].total_token_count = data?.total_token_count || ''
      } else {
        // 5.15 处理其他类型的事件，直接添加新记录
        position += 1
        agent_thoughts.push({
          id: event_id,
          position: position,
          event: event_name,
          thought: data?.thought || '',
          observation: data?.observation || '',
          tool: data?.tool || '',
          tool_input: data?.tool_input || {},
          latency: data?.latency || 0,
          created_at: 0,
        })
      }

      // 5.16 直接修改数组触发响应式更新
      messages.value[0].agent_thoughts = [...agent_thoughts]

      // 5.17 等待DOM更新后再滚动，避免高度未重算导致滚不到底部
      scrollToBottom()
    }
  }).finally(() => {
    active_message_id.value = ''
  })

  // 5.18 响应结束后再次滚动到稳定位置，覆盖建议问题渲染带来的高度变化
  await scrollToBottomUntilStable()

  // 5.19 判断是否开启建议问题生成，如果开启了则非阻塞发起请求，生成期间展示占位
  if (props.suggested_after_answer.enable && message_id.value) {
    handleGenerateSuggestedQuestions(message_id.value)
      .catch(() => {})
      .finally(() => scrollToBottomUntilStable())
  }
  // 5.20 检测是否自动播放，如果是则调用hooks播放音频
  if (props.text_to_speech.enable && props.text_to_speech.auto_play && message_id.value) {
    startAudioStream(message_id.value)
  }
}

// 6.定义停止调试会话函数
const handleStop = async () => {
  // 6.1 如果没有任务id或者未在加载中，则直接停止
  if (task_id.value === '' || !debugChatLoading.value) return

  // 6.2 调用api接口中断请求
  await handleStopDebugChat(props.app?.id, task_id.value)
}

// 7.定义问题提交函数
const handleSubmitQuestion = async (question: string) => {
  // 1.将问题同步到query中
  query.value = question

  // 2.触发handleSubmit函数
  await handleSubmit()
}

// 8.定义文件上传触发器
const triggerFileInput = () => {
  // 1.检测上传的图片数量是否超过5
  if (image_urls.value.length >= 5) {
    Message.error('对话上传图片数量不能超过5张')
    return
  }

  // 2.满足条件触发上传
  fileInput.value.click()
}

// 9.定义文件变化监听器
const handleFileChange = async (event: Event) => {
  // 1.判断是否在上传中
  if (uploadFileLoading.value) return

  // 2.获取当前选中的图片
  const input = event.target as HTMLInputElement
  const selectedFile = input.files?.[0]
  if (selectedFile) {
    try {
      // 3.调用API接口上传图片
      uploadFileLoading.value = true
      const resp = await uploadImage(selectedFile)
      image_urls.value.push(resp.data.image_url)
      Message.success('上传图片成功')
    } finally {
      uploadFileLoading.value = false
    }
  }
}

// 10.开始录音处理器
const handleStartRecord = async () => {
  // 10.1 创建AudioRecorder
  recorder = new AudioRecorder()

  // 10.2 开始录音并记录录音状态
  try {
    isRecording.value = true
    await recorder.start()
    Message.success('开始录音')
  } catch (error: any) {
    Message.error(`录音失败: ${error}`)
    isRecording.value = false
  }
}

// 11.停止录音处理器
const handleStopRecord = async () => {
  if (recorder) {
    try {
      // 11.1 等待录音停止并获取录音数据
      await recorder.stop()
      audioBlob.value = recorder.getWAVBlob()

      // 11.2 调用语音转文本处理器并将文本填充到query中
      await handleAudioToText(audioBlob.value)
      Message.success('语音转文本成功')
      query.value = text.value
    } catch (error: any) {
      Message.error(`录音失败: ${error}`)
    } finally {
      isRecording.value = false // 标记为停止录音
    }
  }
}

// 6.页面DOM加载完毕时初始化数据
onMounted(async () => {
  await loadDebugConversationMessages(String(route.params?.app_id), true)
  await scrollToBottomUntilStable()
})

// 11.页面卸载后停止播放
onUnmounted(() => {
  stopAudioStream()
})
</script>

<template>
  <div class="">
    <!-- 历史对话列表 -->
    <div
      v-if="messages.length > 0"
      :class="`flex flex-col px-6 ${image_urls.length > 0 ? 'h-[calc(100vh-288px)]' : 'h-[calc(100vh-238px)]'}`"
    >
      <dynamic-scroller
        ref="scroller"
        :items="messages.slice().reverse()"
        :min-item-size="88"
        @scroll="handleScroll"
        class="h-full scrollbar-w-none"
      >
        <template v-slot="{ item, index, active }">
          <dynamic-scroller-item
            :item="item"
            :active="active"
            :size-dependencies="[item.answer, item.agent_thoughts?.length]"
          >
            <div class="flex flex-col gap-6 py-6">
              <human-message
                :query="item.query"
                :image_urls="item.image_urls"
                :account="accountStore.account"
              />
              <ai-message
                :agent_thoughts="item.agent_thoughts"
                :answer="item.answer"
                :app="props.app"
                :suggested_questions="item.id === message_id ? suggested_questions : []"
                :suggested_questions_loading="item.id === message_id && suggestedQuestionsLoading"
                :loading="item.id === active_message_id"
                @select-suggested-question="handleSubmitQuestion"
                :latency="item.latency"
                :total_token_count="item.total_token_count"
              />
            </div>
          </dynamic-scroller-item>
        </template>
      </dynamic-scroller>
      <!-- 停止调试会话 -->
      <div v-if="task_id && debugChatLoading" class="h-[50px] flex items-center justify-center">
        <a-button :loading="stopDebugChatLoading" class="rounded-lg px-2" @click="handleStop">
          <template #icon>
            <icon-poweroff />
          </template>
          停止响应
        </a-button>
      </div>
    </div>
    <!-- 对话列表为空时展示的对话开场白 -->
    <div
      v-else
      :class="`flex flex-col p-6 gap-2 items-center justify-center ${image_urls.length > 0 ? 'h-[calc(100vh-288px)]' : 'h-[calc(100vh-238px)]'}`"
    >
      <!-- 应用图标与名称 -->
      <div class="flex flex-col items-center gap-2">
        <a-avatar :size="48" shape="square" class="rounded-lg" :image-url="props.app?.icon" />
        <div class="text-lg text-gray-700">{{ props.app?.name }}</div>
      </div>
      <!-- 对话开场白 -->
      <div
        v-if="props.opening_statement"
        class="bg-gray-100 w-full px-4 py-3 rounded-lg text-gray-700"
      >
        {{ props.opening_statement }}
      </div>
      <!-- 开场白建议问题 -->
      <div class="flex items-center flex-wrap gap-2 w-full">
        <div
          v-for="(opening_question, idx) in props.opening_questions.filter(
            (item) => item.trim() !== '',
          )"
          :key="idx"
          class="px-4 py-1.5 border rounded-lg text-gray-700 cursor-pointer hover:bg-gray-50"
          @click="async () => await handleSubmitQuestion(opening_question)"
        >
          {{ opening_question }}
        </div>
      </div>
    </div>
    <div class="w-full flex flex-col flex-shrink-0">
      <!-- 顶部输入框 -->
      <div class="px-6 flex items-center gap-4">
        <!-- 清除按钮 -->
        <a-button
          :loading="deleteDebugConversationLoading"
          class="flex-shrink-0 !text-gray-700"
          type="text"
          shape="circle"
          @click="
            async () => {
              // 1.先调用停止响应接口
              await handleStop()

              // 2.调用api接口清空会话
              await handleDeleteDebugConversation(props.app?.id)

              // 3.重新获取数据
              await loadDebugConversationMessages(props.app?.id, true)
            }
          "
        >
          <template #icon>
            <icon-empty :size="16" />
          </template>
        </a-button>
        <!-- 输入框组件 -->
        <div
          :class="`${image_urls.length > 0 ? 'h-[100px]' : 'h-[50px]'} flex flex-col justify-center gap-2 px-4 flex-1 border border-gray-200 rounded-[24px]`"
        >
          <!-- 图片列表 -->
          <div v-if="image_urls.length > 0" class="flex items-center gap-2">
            <div
              v-for="(image_url, idx) in image_urls"
              :key="image_url"
              class="w-10 h-10 relative rounded-lg overflow-hidden group cursor-pointer"
            >
              <a-avatar shape="square" :image-url="image_url" />
              <div
                class="hidden group-hover:flex items-center justify-center bg-gray-700/50 w-10 h-10 absolute top-0"
              >
                <icon-close class="text-white" @click="() => image_urls.splice(idx, 1)" />
              </div>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <input
              v-model="query"
              type="text"
              class="flex-1 outline-0"
              @keyup.enter="handleSubmit"
            />
            <!-- 上传图片输入框 -->
            <input
              type="file"
              ref="fileInput"
              accept="image/*"
              @change="handleFileChange"
              class="hidden"
            />
            <a-button
              :loading="uploadFileLoading"
              size="mini"
              type="text"
              shape="circle"
              class="!text-gray-700"
              @click="triggerFileInput"
            >
              <template #icon>
                <icon-plus />
              </template>
            </a-button>
            <!-- 语音转文本加载按钮 -->
            <template v-if="audioToTextLoading">
              <a-button size="mini" type="text" shape="circle">
                <template #icon>
                  <icon-loading />
                </template>
              </a-button>
            </template>
            <template v-else>
              <!-- 开始音频录制按钮 -->
              <a-button
                v-if="!isRecording"
                size="mini"
                type="text"
                shape="circle"
                class="!text-gray-700"
                @click="handleStartRecord"
              >
                <template #icon>
                  <icon-voice />
                </template>
              </a-button>
              <!-- 结束音频录制按钮 -->
              <a-button v-else size="mini" type="text" shape="circle" @click="handleStopRecord">
                <template #icon>
                  <icon-pause />
                </template>
              </a-button>
            </template>
            <a-button
              :loading="debugChatLoading"
              type="text"
              shape="circle"
              class="!text-gray-700"
              @click="handleSubmit"
            >
              <template #icon>
                <icon-send :size="16" />
              </template>
            </a-button>
          </div>
        </div>
      </div>
      <!-- 底部提示信息 -->
      <div class="text-center text-gray-500 text-xs py-4">
        内容由AI生成，无法确保真实准确，仅供参考。
      </div>
    </div>
    <!-- 停止会话按钮 -->
  </div>
</template>

<style scoped></style>
