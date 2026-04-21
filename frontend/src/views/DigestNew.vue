<template>
  <div class="digest-new">
    <h2>信息录入</h2>

    <n-form ref="formRef" :model="form" :rules="rules" :disabled="loading">
      <n-form-item label="来源类型" path="sourceType">
        <n-radio-group v-model:value="form.sourceType">
          <n-radio-button value="text">文本</n-radio-button>
          <n-radio-button value="url">URL</n-radio-button>
        </n-radio-group>
      </n-form-item>
      <n-form-item :label="form.sourceType === 'url' ? 'URL 地址' : '文本内容'" path="content">
        <n-input v-model:value="form.content" :type="form.sourceType === 'text' ? 'textarea' : 'text'"
          :placeholder="form.sourceType === 'url' ? '请输入 URL 地址' : '请输入或粘贴文本内容...'" :rows="8" show-count
          maxlength="50000" />
      </n-form-item>
      <n-form-item label="标题（可选）" path="title">
        <n-input v-model:value="form.title" placeholder="可选，不填则自动生成" />
      </n-form-item>
      <n-form-item>
        <n-space>
          <n-button type="primary" @click="handleSubmit" :loading="loading" :disabled="loading">
            {{ loading && polling ? `处理中 (${pollCount}s)` : '提交处理' }}
          </n-button>
          <n-button @click="handleReset" :disabled="loading">清空</n-button>
        </n-space>
      </n-form-item>
    </n-form>

    <div v-if="polling && !result" class="processing-hint">
      <n-spin size="small" />
      <span>AI 正在处理中，请稍候...</span>
    </div>

    <div v-if="result" class="result-section">
      <n-divider>处理结果</n-divider>
      <n-card>
        <template #header>
          <n-space align="center">
            <n-tag :type="statusType(result.status)" round>
              {{ statusLabel(result.status) }}
            </n-tag>
            <span class="task-id">{{ result.task_id?.slice(0, 12) }}...</span>
          </n-space>
        </template>

        <n-alert v-if="result.error_msg" type="error" :title="result.error_msg" />

        <template v-else>
          <n-descriptions label-placement="left" bordered :column="1">
            <n-descriptions-item label="摘要">
              {{ result.summary || '暂无摘要' }}
            </n-descriptions-item>
          </n-descriptions>

          <n-divider title-placement="left">标签</n-divider>
          <n-space v-if="result.tags?.length">
            <n-tag v-for="tag in result.tags" :key="typeof tag === 'string' ? tag : tag.name || tag.id" type="info"
              round>{{ typeof tag === 'string' ? tag : tag.name || tag }}</n-tag>
          </n-space>
          <n-text v-else depth="3">无标签</n-text>

          <n-divider title-placement="left">行动项 ({{ result.action_items?.length || 0 }})</n-divider>
          <n-list v-if="result.action_items?.length" bordered>
            <n-list-item v-for="(item, index) in result.action_items" :key="index">
              <template #prefix>
                <n-tag :type="priorityColor(item.priority)" size="small" round>
                  {{ item.priority }}
                </n-tag>
              </template>
              <span>{{ item.content }}</span>
            </n-list-item>
          </n-list>
          <n-text v-else depth="3">无行动项</n-text>
        </template>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useMessage } from 'naive-ui'
import api from '@/api'

const message = useMessage()
const loading = ref(false)
const polling = ref(false)
const pollCount = ref(0)
const result = ref<any>(null)

const form = reactive({
  sourceType: 'text',
  content: '',
  title: '',
})

const rules = {
  content: {
    required: true,
    message: '请输入内容',
    trigger: ['blur', 'input'],
  },
}

function priorityColor(priority: string): 'error' | 'warning' | 'default' {
  const map: Record<string, any> = { high: 'error', medium: 'warning', low: 'default' }
  return map[priority] || 'default'
}

function statusType(status: string): 'success' | 'warning' | 'error' | 'default' {
  const map: Record<string, any> = { done: 'success', processing: 'warning', failed: 'error', parse_error: 'error' }
  return map[status] || 'default'
}

function statusLabel(status: string): string {
  const map: Record<string, string> = { done: '已完成', processing: '处理中', failed: '失败', parse_error: '解析错误' }
  return map[status] || status
}

async function handleSubmit() {
  if (!form.content.trim()) {
    message.warning('请输入内容')
    return
  }

  const content = form.content.trim()
  if (form.sourceType === 'url' && !/^https?:\/\//i.test(content)) {
    message.warning('请输入有效的 URL（以 http:// 或 https:// 开头）')
    return
  }

  loading.value = true
  polling.value = false
  pollCount.value = 0
  result.value = null

  try {
    const res: any = await api.post('/digest', {
      source_type: form.sourceType,
      content,
      title: form.title?.trim() || null,
    })

    const taskId = res.task_id
    message.success('提交成功，正在处理...')

    pollResult(taskId)
  } catch (e: any) {
    message.error(e.message || e.response?.data?.message || '提交失败')
    loading.value = false
  }
}

async function pollResult(taskId: string, attempts = 0) {
  if (attempts > 60) {
    message.error('处理超时，请稍后在知识卡片列表查看结果')
    loading.value = false
    polling.value = false
    return
  }

  polling.value = true
  pollCount.value = attempts * 2

  await new Promise((r) => setTimeout(r, 2000))

  try {
    const res: any = await api.get(`/digest/${taskId}`)
    result.value = res

    if (res.status === 'processing') {
      pollResult(taskId, attempts + 1)
    } else {
      loading.value = false
      polling.value = false
      if (res.status === 'done') {
        message.success('处理完成！')
      } else {
        message.warning(`处理状态: ${statusLabel(res.status)}`)
      }
    }
  } catch (e: any) {
    if (attempts > 5) {
      message.error('获取结果失败，请稍后重试')
      loading.value = false
      polling.value = false
      return
    }
    pollResult(taskId, attempts + 1)
  }
}

function handleReset() {
  if (loading.value) return
  form.content = ''
  form.title = ''
  result.value = null
  polling.value = false
}
</script>

<style scoped>
.digest-new h2 {
  margin-bottom: 20px;
  color: #89b4fa;
}

.processing-hint {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  padding: 12px 16px;
  background: #181825;
  border-radius: 6px;
  color: #a6adc8;
  font-size: 14px;
}

.result-section {
  margin-top: 24px;
}

.task-id {
  font-size: 12px;
  color: #6c7086;
  font-family: monospace;
}
</style>
