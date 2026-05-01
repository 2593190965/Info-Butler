<template>
  <div class="digest-new">
    <h2>信息录入</h2>

    <n-tabs v-model:value="activeTab" type="line" :disabled="loading">
      <n-tab-pane name="text" tab="文本/URL">
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
          <n-form-item label="生成选项">
            <n-space>
              <n-checkbox v-model:checked="form.generateActions">
                生成行动项
              </n-checkbox>
              <n-checkbox v-model:checked="form.generateTags">
                生成标签
              </n-checkbox>
            </n-space>
          </n-form-item>
          <n-form-item>
            <n-space>
              <n-button type="primary" @click="handleSubmit" :loading="loading && !polling" :disabled="loading">
                {{ loading && polling ? `处理中 (${pollCount}s)` : '提交处理' }}
              </n-button>
              <n-button @click="handleReset" :disabled="loading">清空</n-button>
            </n-space>
          </n-form-item>
        </n-form>
      </n-tab-pane>

      <n-tab-pane name="file" tab="文件上传">
        <div class="upload-area" @click="triggerFileInput" @dragover.prevent @drop.prevent="handleDrop">
          <input ref="fileInputRef" type="file" class="file-input" accept=".pdf,.docx,.xlsx,.txt,.md"
            @change="handleFileSelect" />
          <n-icon size="48" color="#a6adc8">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </n-icon>
          <p class="upload-text">点击或拖拽文件到此区域</p>
          <p class="upload-hint">支持 PDF、Word、Excel、TXT、Markdown（最大 10MB）</p>
        </div>
        <div v-if="selectedFile" class="file-info">
          <n-space align="center">
            <n-tag type="info" round>{{ getFileExtension(selectedFile.name) }}</n-tag>
            <span>{{ selectedFile.name }}</span>
            <span class="file-size">({{ formatFileSize(selectedFile.size) }})</span>
            <n-button size="small" @click="handleUploadFile" :loading="uploading">上传并处理</n-button>
            <n-button size="small" @click="clearFile" :disabled="uploading">移除</n-button>
          </n-space>
        </div>
        <n-form-item label="生成选项" v-if="selectedFile">
          <n-space>
            <n-checkbox v-model:checked="form.generateActions">
              生成行动项
            </n-checkbox>
            <n-checkbox v-model:checked="form.generateTags">
              生成标签
            </n-checkbox>
          </n-space>
        </n-form-item>
      </n-tab-pane>
    </n-tabs>

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

      <div v-if="result.status === 'done'" class="detail-link">
        <n-button text type="primary" @click="router.push(`/digest/${result.task_id}`)">
          查看完整详情 →
        </n-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import api from '@/api'

const router = useRouter()
const message = useMessage()
const loading = ref(false)
const polling = ref(false)
const pollCount = ref(0)
const result = ref<any>(null)
const activeTab = ref('text')
const fileInputRef = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const uploading = ref(false)

const form = reactive({
  sourceType: 'text',
  content: '',
  title: '',
  generateActions: true,
  generateTags: true,
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

function getFileExtension(filename: string): string {
  return filename.split('.').pop()?.toUpperCase() || ''
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
  }
}

function handleDrop(event: DragEvent) {
  if (event.dataTransfer && event.dataTransfer.files.length > 0) {
    selectedFile.value = event.dataTransfer.files[0]
  }
}

function clearFile() {
  selectedFile.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

async function handleUploadFile() {
  if (!selectedFile.value) {
    message.warning('请先选择文件')
    return
  }

  const maxSize = 10 * 1024 * 1024
  if (selectedFile.value.size > maxSize) {
    message.error('文件大小超过限制（10MB）')
    return
  }

  uploading.value = true
  loading.value = true
  polling.value = false
  pollCount.value = 0
  result.value = null

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('generate_actions', String(form.generateActions))
    formData.append('generate_tags', String(form.generateTags))

    const res: any = await api.post('/digest/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    const taskId = res.task_id
    message.success('文件上传成功，正在处理...')

    pollResult(taskId)
  } catch (e: any) {
    message.error(e.message || e.response?.data?.message || '上传失败')
    loading.value = false
    uploading.value = false
  }
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
      generate_actions: form.generateActions,
      generate_tags: form.generateTags,
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
    uploading.value = false
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
      uploading.value = false
      if (res.status === 'done') {
        message.success('处理完成！')
      } else {
        message.warning(`处理状态: ${statusLabel(res.status)}`)
      }
    }
  } catch (e: any) {
    if (e.response?.status === 404) {
      message.error('处理失败，记录已删除')
      loading.value = false
      polling.value = false
      uploading.value = false
      return
    }
    if (attempts > 5) {
      message.error('获取结果失败，请稍后重试')
      loading.value = false
      polling.value = false
      uploading.value = false
      return
    }
    pollResult(taskId, attempts + 1)
  }
}

function handleReset() {
  if (loading.value) return
  form.content = ''
  form.title = ''
  form.generateActions = true
  form.generateTags = true
  result.value = null
  polling.value = false
  clearFile()
}
</script>

<style scoped>
.digest-new h2 {
  margin-bottom: 20px;
  color: #89b4fa;
}

.upload-area {
  border: 2px dashed #45475a;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s;
}

.upload-area:hover {
  border-color: #89b4fa;
}

.file-input {
  display: none;
}

.upload-text {
  margin-top: 12px;
  font-size: 16px;
  color: #cdd6f4;
}

.upload-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #6c7086;
}

.file-info {
  margin-top: 16px;
  padding: 12px;
  background: #181825;
  border-radius: 6px;
}

.file-size {
  color: #6c7086;
  font-size: 12px;
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

.detail-link {
  text-align: center;
  margin-top: 12px;
}
</style>
