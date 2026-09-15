import { nextTick, onBeforeUnmount, type Ref } from 'vue'

export const useScrollToBottomUntilStable = (scroller: Ref<any>) => {
  let timer: ReturnType<typeof setInterval> | undefined

  const stop = () => {
    if (timer) {
      clearInterval(timer)
      timer = undefined
    }
  }

  // 1.生成临时的消息id，避免多条待回复消息的id均为空造成虚拟滚动key冲突
  const createPendingId = () => `pending-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`

  // 2.DOM更新后滚动到底部，用于SSE流式回调这类高频场景
  const scrollToBottom = () => {
    nextTick(() => scroller.value?.scrollToBottom())
  }

  // 3.等待DOM更新后持续滚动，直到滚动高度稳定，用于发送消息与响应结束后的兜底
  const scrollToBottomUntilStable = async () => {
    await nextTick()
    scroller.value?.scrollToBottom()
    stop()
    const startedAt = Date.now()
    let stableRounds = 0
    let lastHeight = -1
    timer = setInterval(() => {
      const el = scroller.value?.$el as HTMLElement | undefined
      if (!el) {
        stop()
        return
      }
      const height = el.scrollHeight
      const atBottom = height - el.scrollTop - el.clientHeight <= 2
      stableRounds = atBottom && height === lastHeight ? stableRounds + 1 : 0
      lastHeight = height
      if (stableRounds >= 2 || Date.now() - startedAt > 3000) {
        stop()
        return
      }
      scroller.value?.scrollToBottom()
    }, 80)
  }

  onBeforeUnmount(stop)

  return { createPendingId, scrollToBottom, scrollToBottomUntilStable }
}
