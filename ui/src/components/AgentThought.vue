<script setup lang="ts">
import { computed, ref, type PropType } from 'vue'
import { QueueEvent } from '@/config'

// 1.定义自定义组件所需数据
const props = defineProps({
  loading: { type: Boolean, default: false, required: false },
  agent_thoughts: {
    type: Array as PropType<Record<string, any>[]>,
    default: () => [],
    required: true,
  },
})

// 2.事件与展示元信息的映射，涵盖：语义标题、图标、强调色
const event_meta_map: Record<string, { title: string; icon: string; accent: string }> = {
  [QueueEvent.longTermMemoryRecall]: {
    title: '长期记忆召回',
    icon: 'icon-history',
    accent: 'text-purple-600',
  },
  [QueueEvent.agentThought]: { title: '思考', icon: 'icon-bulb', accent: 'text-amber-600' },
  [QueueEvent.datasetRetrieval]: {
    title: '检索知识库',
    icon: 'icon-search',
    accent: 'text-teal-600',
  },
  [QueueEvent.agentAction]: { title: '调用工具', icon: 'icon-tool', accent: 'text-blue-600' },
  [QueueEvent.agentMessage]: { title: '生成回答', icon: 'icon-message', accent: 'text-green-600' },
  [QueueEvent.error]: { title: '执行出错', icon: 'icon-close-circle', accent: 'text-red-600' },
}

// 3.折叠状态下最大展示的步骤数
const COLLAPSED_STEP_COUNT = 3

const expanded_keys = ref<Record<string, boolean>>({})
const show_all = ref(false)
const collapsed = ref(false)

// 4.尝试将内容解析成可读的JSON字符串，解析失败则原样返回
const format_content = (content: string) => {
  if (!content) return ''
  try {
    return JSON.stringify(JSON.parse(content), null, 2)
  } catch {
    return content
  }
}

// 5.从agent_thought事件中提取工具调用列表，该事件的thought字段是tool_calls的JSON字符串
const extract_tool_calls = (thought: string): Record<string, any>[] => {
  if (!thought) return []
  try {
    const parsed = JSON.parse(thought)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

// 6.提取步骤需要展示的工具名
const get_tool_name = (step: Record<string, any>) => {
  if (step.tool) return String(step.tool)
  const names = extract_tool_calls(step.thought)
    .map((item) => item?.name)
    .filter(Boolean)
  return names.length > 0 ? names.join('、') : ''
}

// 7.提取步骤需要展示的工具入参摘要，仅保留前2个参数并做短截断，完整参数在展开详情中查看
const get_tool_args = (step: Record<string, any>) => {
  const raw_args =
    step.tool_input && Object.keys(step.tool_input).length > 0
      ? step.tool_input
      : (extract_tool_calls(step.thought)[0]?.args ?? {})

  const parts = Object.entries(raw_args)
    .slice(0, 2)
    .map(([key, value]) => {
      const text = typeof value === 'string' ? value : JSON.stringify(value)
      return `${key}: ${text.length > 16 ? `${text.slice(0, 16)}…` : text}`
    })
  if (parts.length === 0) return ''

  const text = parts.join('  ')
  return text.length > 32 ? `${text.slice(0, 32)}…` : text
}

// 8.格式化步骤耗时，兼容缺失字段的场景
const format_latency = (latency: any) => {
  const value = Number(latency)
  if (!Number.isFinite(value)) return ''
  return `${value.toFixed(2)}s`
}

// 9.构建步骤列表，涵盖：序号、状态、标题、工具信息与详情
const steps = computed(() => {
  const thoughts = (props.agent_thoughts ?? []).filter((item) => event_meta_map[item?.event])

  return thoughts.map((item, idx) => {
    const meta = event_meta_map[item.event]
    const is_last = idx === thoughts.length - 1
    const status = item.event === QueueEvent.error ? 'error' : props.loading && is_last ? 'running' : 'done'

    return {
      key: `${item.id ?? ''}-${idx}`,
      index: item.position ?? idx + 1,
      event: item.event,
      title: meta.title,
      icon: meta.icon,
      accent: meta.accent,
      status: status,
      tool_name: get_tool_name(item),
      tool_args: get_tool_args(item),
      latency: format_latency(item.latency),
      detail: [
        { label: '入参', content: format_content(JSON.stringify(item.tool_input ?? {})) },
        { label: '返回', content: format_content(item.observation ?? '') },
        { label: '内容', content: format_content(item.thought ?? '') },
      ].filter((detail) => detail.content !== '' && detail.content !== '{}'),
    }
  })
})

// 10.计算实际渲染的步骤，运行中与展开状态下展示全部
const visible_steps = computed(() => {
  if (props.loading || show_all.value || steps.value.length <= COLLAPSED_STEP_COUNT) {
    return steps.value
  }
  return steps.value.slice(0, COLLAPSED_STEP_COUNT)
})

const hidden_count = computed(() => steps.value.length - visible_steps.value.length)

// 11.累计耗时，仅统计已完成的步骤
const total_latency = computed(() => {
  const total = steps.value.reduce((acc, step) => acc + (parseFloat(step.latency) || 0), 0)
  return total > 0 ? `${total.toFixed(2)}s` : ''
})

// 12.切换步骤详情的展开状态
const toggle_detail = (key: string) => {
  expanded_keys.value = { ...expanded_keys.value, [key]: !expanded_keys.value[key] }
}
</script>

<template>
  <!-- 智能体推理步骤，以时间线形式内联展示 -->
  <div v-if="steps.length > 0" class="w-full max-w-full">
    <div
      class="flex items-center gap-2 text-xs text-gray-500 cursor-pointer select-none w-fit"
      @click="collapsed = !collapsed"
    >
      <icon-right v-if="collapsed" />
      <icon-down v-else />
      <span>思考过程 · {{ steps.length }} 步</span>
      <span v-if="total_latency">· {{ total_latency }}</span>
      <icon-loading v-if="props.loading" />
    </div>

    <div v-if="!collapsed" class="mt-2 flex flex-col">
      <div v-for="step in visible_steps" :key="step.key" class="flex gap-2">
        <!-- 左侧状态轴 -->
        <div class="flex flex-col items-center flex-shrink-0">
          <div
            :class="`w-[18px] h-[18px] rounded-full flex items-center justify-center flex-shrink-0 ${
              step.status === 'error'
                ? 'bg-red-100 text-red-600'
                : step.status === 'running'
                  ? 'bg-blue-100 text-blue-600'
                  : 'bg-gray-100 text-gray-500'
            }`"
          >
            <icon-loading v-if="step.status === 'running'" :size="11" />
            <icon-close v-else-if="step.status === 'error'" :size="11" />
            <icon-check v-else :size="11" />
          </div>
          <div v-if="step.key !== visible_steps[visible_steps.length - 1].key" class="w-px flex-1 bg-gray-200 my-0.5" />
        </div>

        <!-- 右侧步骤内容 -->
        <div class="flex-1 min-w-0 pb-3">
          <div class="flex items-start gap-2">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-1.5 flex-wrap">
                <component :is="step.icon" :size="13" :class="step.accent" />
                <span
                  :class="`text-[13px] ${step.status === 'running' ? 'text-blue-600' : step.status === 'error' ? 'text-red-600' : 'text-gray-700'}`"
                >
                  {{ step.title }}
                </span>
                <span v-if="step.tool_name" class="text-[13px] text-gray-700 font-mono">
                  {{ step.tool_name }}
                </span>
              </div>
              <div
                v-if="step.tool_args"
                class="text-xs text-gray-400 font-mono truncate"
                :title="step.tool_args"
              >
                {{ step.tool_args }}
              </div>
            </div>
            <div class="flex items-center gap-1 flex-shrink-0">
              <span v-if="step.latency" class="text-xs text-gray-400">{{ step.latency }}</span>
              <icon-down
                v-if="step.detail.length > 0 && !expanded_keys[step.key]"
                class="text-gray-400 cursor-pointer"
                :size="12"
                @click="toggle_detail(step.key)"
              />
              <icon-up
                v-else-if="step.detail.length > 0"
                class="text-gray-400 cursor-pointer"
                :size="12"
                @click="toggle_detail(step.key)"
              />
            </div>
          </div>

          <!-- 步骤详情 -->
          <div v-if="expanded_keys[step.key] && step.detail.length > 0" class="mt-1.5 flex flex-col gap-1.5">
            <div v-for="detail in step.detail" :key="detail.label">
              <div class="text-xs text-gray-400">{{ detail.label }}</div>
              <pre
                class="mt-0.5 text-xs text-gray-500 bg-gray-50 border border-gray-100 rounded-lg p-2 max-h-40 overflow-auto whitespace-pre-wrap break-all font-mono"
                >{{ detail.content }}</pre
              >
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 展开剩余步骤 -->
    <div
      v-if="!collapsed && hidden_count > 0"
      class="flex items-center gap-1 text-xs text-gray-500 cursor-pointer hover:text-gray-700 w-fit"
      @click="show_all = true"
    >
      <icon-down :size="12" />
      展开剩余 {{ hidden_count }} 步
    </div>
  </div>
</template>

<style scoped></style>
