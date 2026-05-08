<script setup lang="ts">
import { onUnmounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { uploadFile } from '@/services/upload-file'
import { createDocuments, getDocumentsStatus } from '@/services/dataset'
import { type Form, Message } from '@arco-design/web-vue'
import { unescapeString } from '@/utils/helper'

// 1.定义页面逻辑基础数据，涵盖定时器、路由、当前步骤数、表单信息、接口加载状态
let timer = null // 定时器，默认为空
let batch = '' // 批处理标识
const route = useRoute()
const currentStep = ref(1)
const createDocumentsForm = reactive({
  file_list: [], // 上传文件列表
  process_type: 'automatic', // 处理类型
  rule: {
    separators: ['\\n'],
    chunk_size: 500,
    chunk_overlap: 50,
    pre_process_rules: [],
  },
})
const customRuleFormRef = ref<InstanceType<typeof Form>>()
const createDocumentsLoading = ref(false)
const documents = reactive<Array<any>>([])
let fetchCount = 0

// 2.定义下一步处理函数
const nextStep = async () => {
  // 2.1 判断当前所处的步骤并执行不同的检查
  if (currentStep.value === 1) {
    // 2.2 检查是否已经上传了文件，如果没上传则不允许点击下一步并提示
    if (createDocumentsForm.file_list.length === 0) {
      Message.error('请上传需要处理的文件')
      return
    }
    // 2.3检查文件是否上传完毕
    const isUploaded = createDocumentsForm.file_list.every(
      (fileItem) => fileItem.response?.data?.id,
    )
    if (!isUploaded) {
      Message.warning('文件正在上传中，请稍等')
      return
    }

    // 2.4 进入下一步
    currentStep.value++
  } else {
    // 2.4 当前处于第2页，判断对应的表单逻辑是否正确
    if (createDocumentsForm.process_type === 'custom') {
      // 2.5 校验表单数据监测是否出错，如果出错则停止程序
      const errors = await customRuleFormRef.value?.validate()
      if (errors) return
    }

    // 2.6 如果校验成功或者是自动规则，则继续后续的步骤
    try {
      // 2.7 将加载状态设置为true并处理请求数据
      createDocumentsLoading.value = true
      const req = {
        upload_file_ids: createDocumentsForm.file_list.map((fileItem) => fileItem.response.data.id),
        process_type: createDocumentsForm.process_type,
      }

      // 2.8 如果处理类型为自定义，则添加上处理规则
      if (createDocumentsForm.process_type === 'custom') {
        // 处理转义的分隔符为非转义数据
        req.rule = {
          pre_process_rules: [
            {
              id: 'remove_extra_space',
              enabled: createDocumentsForm.rule.pre_process_rules.includes('remove_extra_space'),
            },
            {
              id: 'remove_url_and_email',
              enabled: createDocumentsForm.rule.pre_process_rules.includes('remove_url_and_email'),
            },
          ],
          segment: {
            separators: createDocumentsForm.rule.separators.map((separator) =>
              unescapeString(separator),
            ),
            chunk_size: createDocumentsForm.rule.chunk_size,
            chunk_overlap: createDocumentsForm.rule.chunk_overlap,
          },
        }
      }

      // 2.8 发起请求并获取预处理批次
      const resp = await createDocuments(route.params?.dataset_id as string, req)
      batch = resp.data.batch

      // 2.9 先调用一次获取文档状态数据，然后创建定时器
      await fetDocumentsStatus()
      startTimer()

      // 创建文档列表预处理成功，步骤+1
      currentStep.value++
    } finally {
      createDocumentsLoading.value = false
    }
  }
}

// 3.定义获取文档状态函数
const fetDocumentsStatus = async () => {
  // 3.1 调用接口获取文档状态数据
  fetchCount++
  const resp = await getDocumentsStatus(route.params?.dataset_id, batch)
  const data = resp.data

  // 3.2 同步文档状态信息
  documents.splice(0, documents.length, ...data)

  // 3.3 如果请求次数超过限制则停止
  if (fetchCount >= 30) stopTimer()

  // 3.4 如果文档都处理完毕（处理完成或者出错）则停止
  const isCompleted = data.every(
    (document) => document.status === 'completed' || document.status === 'error',
  )
  if (isCompleted) stopTimer()
}

// 5.定义开始定时器函数
const startTimer = () => (timer = setInterval(fetDocumentsStatus, 5000))

// 6.定义停止定时器函数
const stopTimer = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

// 7.页面卸载时同步卸载定时器
onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
})
</script>

<template>
  <div class="p-6">
    <!-- 回退按钮与标题 -->
    <div class="flex items-center mb-6 gap-4">
      <!-- 左侧回退按钮 -->
      <router-link
        :to="{
          name: 'space-datasets-documents-list',
          params: { dataset_id: route.params?.dataset_id as string },
        }"
      >
        <a-button size="mini" type="text" class="!text-gray-700">
          <template #icon>
            <icon-left />
          </template>
        </a-button>
      </router-link>
      <div class="text-lg font-bold text-gray-700">添加文件</div>
    </div>
    <!-- 步骤条 -->
    <div class="w-[520px] mx-auto">
      <a-steps :current="currentStep">
        <a-step>上传</a-step>
        <a-step>分段设置</a-step>
        <a-step>数据处理</a-step>
      </a-steps>
    </div>
    <!-- 步骤条页面 -->
    <div class="min-h-[calc(100vh-160px)] p-[48px]">
      <!-- 上传页面 -->
      <div v-if="currentStep === 1" class="">
        <!-- 上传文件按钮 -->
        <a-upload
          v-model:file-list="createDocumentsForm.file_list"
          draggable
          accept=".doc,.docx,.pdf,.txt,.md,.markdown"
          :limit="10"
          multiple
          tip="支持PDF、TXT、DOC、DOCX、MD，最多可上传10个文件，每个文件的大小不超过10MB"
          :custom-request="
            async (option) => {
              // 1.提取选项中的文件选项以及成功回调
              const { fileItem, onSuccess } = option

              // 2.调用api接口上传文件并添加数据
              const resp = await uploadFile(fileItem.file)
              onSuccess(resp)
            }
          "
        />
      </div>
      <!-- 分段设置页面 -->
      <div v-else-if="currentStep === 2" class="">
        <!-- 自动分段与清洗 -->
        <div
          :class="`px-5 py-4 bg-white rounded-lg border cursor-pointer mb-4 hover:border-blue-700 ${createDocumentsForm.process_type === 'automatic' ? 'border-blue-700' : ''}`"
          @click="createDocumentsForm.process_type = 'automatic'"
        >
          <div class="font-bold text-gray-700 mb-2">自动分段与清洗</div>
          <div class="text-gray-500">自动分段与预处理规则</div>
        </div>
        <!-- 自定义 -->
        <div
          :class="`px-5 py-4 bg-white rounded-lg border cursor-pointer hover:border-blue-700 ${createDocumentsForm.process_type === 'custom' ? 'border-blue-700' : ''}`"
          @click="createDocumentsForm.process_type = 'custom'"
        >
          <div class="font-bold text-gray-700 mb-2">自定义</div>
          <div class="text-gray-500">自定义分段规则、分段长度与预处理规则</div>
          <!-- 自定义表单 -->
          <div v-if="createDocumentsForm.process_type === 'custom'" class="">
            <a-divider />
            <!-- 表单选项 -->
            <a-form :model="createDocumentsForm.rule" ref="customRuleFormRef" layout="vertical">
              <a-form-item
                field="separators"
                label="分段标识符"
                asterisk-position="end"
                :rules="[{ required: '分段标识符不能为空' }]"
              >
                <a-input-tag
                  v-model:model-value="createDocumentsForm.rule.separators"
                  placeholder="请输入分段标识符，按下Enter结束"
                />
              </a-form-item>
              <a-form-item
                field="chunk_size"
                label="分段最大长度"
                required
                asterisk-position="end"
                :rules="[{ required: true, message: '分段最大长度不能为空' }]"
              >
                <a-input-number
                  v-model:model-value="createDocumentsForm.rule.chunk_size"
                  :min="100"
                  :max="1000"
                  :step="1"
                  :default-value="500"
                  placeholder="请输入100-1000的数字"
                />
              </a-form-item>
              <a-form-item
                field="chunk_overlap"
                label="块重叠数"
                required
                asterisk-position="end"
                :rules="[{ required: true, message: '块重叠数不能为空' }]"
              >
                <a-input-number
                  v-model:model-value="createDocumentsForm.rule.chunk_overlap"
                  :min="0"
                  :max="500"
                  :step="1"
                  :default-value="50"
                  placeholder="请输入0-500的数字"
                />
              </a-form-item>
              <a-form-item field="pre_process_rules" label="文本预处理规则">
                <a-checkbox-group
                  v-model:model-value="createDocumentsForm.rule.pre_process_rules"
                  direction="vertical"
                >
                  <a-checkbox value="remove_extra_space">
                    替换掉连续的空格、换行符和制表符
                  </a-checkbox>
                  <a-checkbox value="remove_url_and_email">删除所有 URL 和电子邮件</a-checkbox>
                </a-checkbox-group>
              </a-form-item>
            </a-form>
          </div>
        </div>
      </div>
      <!-- 数据处理页面 -->
      <div v-else class="">
        <!-- 数据处理状态提示 -->
        <div class="text-gray-900 mb-4 text-base">服务器正在处理中</div>
        <!-- 处理中的文档列表 -->
        <div class="flex flex-col gap-2">
          <div
            v-for="document in documents"
            :key="document.id"
            class="flex items-center justify-between px-4 py-3 bg-white rounded-lg border"
          >
            <!-- 左侧文件信息 -->
            <div class="flex items-center gap-2.5">
              <a-avatar shape="square" class="bg-blue-700" :size="32">
                <icon-file />
              </a-avatar>
              <div class="">
                <div class="text-gray-700">{{ document.name }}</div>
                <div class="text-gray-500">{{ (document.size / 1024).toFixed(2) }}kb</div>
              </div>
            </div>
            <!-- 处理的百分比 -->
            <div v-if="document.status === 'completed'" class="text-gray-500">处理完成</div>
            <div v-else-if="document.status === 'error'" class="text-red-700">处理出错</div>
            <div v-else-if="document.segment_count === 0" class="text-gray-500">0%</div>
            <div v-else class="text-gray-500">
              {{ ((document.completed_segment_count / document.segment_count) * 100).toFixed(2) }}%
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 按钮：涵盖上一步和下一步 -->
    <div class="flex items-center justify-between px-[48px]">
      <div class=""></div>
      <div class="flex items-center gap-2">
        <a-button
          v-if="currentStep == 2"
          class="rounded-lg"
          @click="
            () => {
              if (currentStep > 1) currentStep--
            }
          "
        >
          上一步
        </a-button>
        <a-button
          :loading="createDocumentsLoading"
          v-if="currentStep <= 2"
          type="primary"
          class="rounded-lg"
          @click="nextStep"
        >
          下一步
        </a-button>
        <!-- 数据处理页面显示的内容 -->
        <div v-if="currentStep === 3" class="flex items-center gap-2">
          <div class="text-gray-500">点击确认不影响数据处理，处理完毕后可进行引用</div>
          <router-link
            :to="{
              name: 'space-datasets-documents-list',
              params: { dataset_id: route.params?.dataset_id as string },
            }"
          >
            <a-button type="primary" class="rounded-lg">确定</a-button>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
