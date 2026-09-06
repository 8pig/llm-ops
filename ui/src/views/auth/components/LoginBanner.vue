<script setup lang="ts">
const features = [
  { title: '私有化部署', desc: '数据安全可控，全链路留痕' },
  { title: '人机协同', desc: 'AI 输出由执业律师终审' },
  { title: '智能法律检索', desc: '法律研究与文书高效生成' },
]
</script>

<template>
  <div
    class="relative flex w-[600px] shrink-0 overflow-hidden banner-bg text-white select-none"
  >
    <!-- 装饰纹理与光晕 -->
    <div class="pointer-events-none absolute inset-0 banner-grid" aria-hidden="true"></div>
    <div class="pointer-events-none absolute inset-0 banner-glow" aria-hidden="true"></div>

    <div class="relative flex flex-col w-full h-full px-12 pt-16 pb-12">
      <!-- 顶部品牌 -->
      <div class="flex items-center gap-3">
        <div
          class="w-10 h-10 rounded-xl flex items-center justify-center border border-white/20 bg-white/5"
        >
          <svg viewBox="0 0 24 24" class="w-6 h-6" fill="none" aria-hidden="true">
            <path
              d="M12 3v18M12 3l-2.2 2.4M12 3l2.2 2.4M12 6.2v0M6.5 12.5h11M6.5 12.5a2.2 2.2 0 1 0-2.2 2.2M17.5 12.5a2.2 2.2 0 1 1-2.2 2.2"
              stroke="#c6a458"
              stroke-width="1.5"
              stroke-linecap="round"
            />
          </svg>
        </div>
        <div class="flex flex-col leading-tight">
          <span class="text-sm font-semibold tracking-widest">坤盛AI辅助平台</span>
          <span class="text-xs text-white/50">KUNSHENG · LEGAL AI</span>
        </div>
      </div>

      <!-- 中部文案 -->
      <div class="mt-14">
        <div
          class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-[#c6a458]/40 bg-[#c6a458]/10 text-[#e5cf96] text-xs tracking-wide"
        >
          律所智能化协作平台
        </div>
        <h2 class="mt-5 text-[34px] leading-snug font-bold">
          让 AI 成为律师的
          <span class="text-[#e5cf96]">超级副手</span>
        </h2>
        <p class="mt-4 max-w-[420px] text-[15px] leading-7 text-white/65">
          面向律师事务所的一站式智能工作台，将检索、研究与文书起草交给 AI 提效，把终审与责任留给执业律师。
        </p>
      </div>

      <!-- 天平插画 -->
      <div class="flex flex-1 items-center justify-center min-h-0 pt-2 overflow-hidden">
        <svg viewBox="0 0 360 300" class="w-[300px] h-[250px]" fill="none" aria-hidden="true">
          <!-- 光环 -->
          <circle cx="180" cy="150" r="120" stroke="#ffffff" stroke-opacity="0.07" />
          <circle cx="180" cy="150" r="98" stroke="#ffffff" stroke-opacity="0.05" />
          <circle
            cx="180"
            cy="150"
            r="120"
            stroke="#ffffff"
            stroke-opacity="0.12"
            stroke-dasharray="1 10"
            stroke-linecap="round"
          />
          <!-- 背景悬浮元素 -->
          <g stroke="#ffffff" stroke-opacity="0.28" stroke-linecap="round">
            <rect x="34" y="66" width="30" height="42" rx="3" stroke-width="1.5" />
            <path d="M40 78h18M40 86h18M40 94h12" stroke-width="1.5" />
            <circle cx="322" cy="74" r="12" stroke-width="1.5" />
            <path d="M331 83l12 12" stroke-width="1.5" />
            <path d="M34 176h18" stroke-width="1.5" opacity="0.7" />
            <path d="M308 184h20" stroke-width="1.5" opacity="0.7" />
          </g>
          <!-- 立柱与底座 -->
          <g stroke="#ffffff" stroke-width="1.8" stroke-linecap="round">
            <path d="M180 120v130" />
            <path d="M164 250h32" />
            <path d="M155 262h50" />
          </g>
          <!-- 顶部圆球（金色） -->
          <circle cx="180" cy="84" r="5" stroke="#c6a458" stroke-width="1.8" />
          <path d="M180 89v31" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round" />
          <circle cx="180" cy="114" r="6" stroke="#c6a458" stroke-width="1.6" />
          <!-- 平衡梁 -->
          <g stroke="#ffffff" stroke-width="1.8" stroke-linecap="round">
            <path d="M62 120h236" />
            <path d="M62 126h236" opacity="0.35" />
          </g>
          <!-- 左秤盘 -->
          <g stroke="#ffffff" stroke-width="1.5" stroke-linecap="round">
            <path d="M62 122L48 178" />
            <path d="M62 122L76 178" />
            <path d="M36 182q26 30 52 0" stroke-width="1.8" />
            <path d="M40 178h44" opacity="0.4" />
          </g>
          <!-- 右秤盘 -->
          <g stroke="#ffffff" stroke-width="1.5" stroke-linecap="round">
            <path d="M298 122L284 178" />
            <path d="M298 122L312 178" />
            <path d="M272 182q26 30 52 0" stroke-width="1.8" />
            <path d="M276 178h44" opacity="0.4" />
          </g>
          <!-- 底部渐隐 -->
          <defs>
            <linearGradient id="bannerFade" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stop-color="#0a1740" stop-opacity="0" />
              <stop offset="1" stop-color="#0a1740" stop-opacity="1" />
            </linearGradient>
          </defs>
          <rect x="0" y="232" width="360" height="68" fill="url(#bannerFade)" />
        </svg>
      </div>

      <!-- 能力点 -->
      <div class="grid grid-cols-3 gap-4">
        <div
          v-for="feature in features"
          :key="feature.title"
          class="rounded-xl border border-white/10 bg-white/5 px-4 py-3"
        >
          <div class="flex items-center gap-1.5 text-[13px] font-semibold text-white/90">
            <span class="inline-block w-1.5 h-1.5 rounded-full bg-[#c6a458]"></span>
            {{ feature.title }}
          </div>
          <div class="mt-1.5 text-[11px] leading-4 text-white/45">{{ feature.desc }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.banner-bg {
  background:
    radial-gradient(120% 90% at 85% 0%, rgba(30, 64, 175, 0.55) 0%, rgba(30, 64, 175, 0) 55%),
    linear-gradient(135deg, #0a1740 0%, #0d1f55 55%, #16377f 100%);
}

.banner-grid {
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.045) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(80% 80% at 20% 10%, #000 0%, transparent 100%);
}

.banner-glow {
  background: radial-gradient(50% 40% at 90% 85%, rgba(198, 164, 88, 0.14) 0%, transparent 70%);
}
</style>
