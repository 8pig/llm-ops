import { onBeforeUnmount, type Ref } from 'vue'

export const useScrollToBottomUntilStable = (scroller: Ref<any>) => {
  let timer: ReturnType<typeof setInterval> | undefined

  const stop = () => {
    if (timer) {
      clearInterval(timer)
      timer = undefined
    }
  }

  const scrollToBottomUntilStable = () => {
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

  return { scrollToBottomUntilStable }
}
