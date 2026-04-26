<template>
  <div class="digest-detail" v-if="data">
    <n-space align="center" justify="space-between" class="detail-header">
      <n-space align="center" :size="12">
        <n-button text @click="$router.push('/digest/list')">← 返回列表</n-button>
        <h2>{{ data.title || '无标题' }}</h2>
        <n-tag :type="statusType(data.status)" size="small">{{ statusLabel(data.status) }}</n-tag>
      </n-space>
      <n-space align="center">
        <span class="meta">{{ formatTime(data.created_at) }}</span>
        <n-tag v-if="data.source_type === 'url'" size="small" type="info">
          <a v-if="isSafeUrl(data.source_url)" :href="data.source_url" target="_blank" rel="noopener noreferrer" class="source-link">查看原文</a>
          <span v-else>URL 来源</span>
        </n-tag>
      </n-space>
    </n-space>

    <n-card class="section-card">
      <template #header>
        <span class="section-title">摘要</span>
      </template>
      <p class="summary-text">{{ data.summary || '暂无摘要' }}</p>
    </n-card>

    <n-card class="section-card">
      <template #header>
        <n-space align="center">
          <span class="section-title">标签</span>
          <n-tag size="small" round type="info">{{ data.tags?.length || 0 }} 个</n-tag>
        </n-space>
      </template>
      <n-space v-if="data.tags?.length">
        <n-tag v-for="tag in data.tags" :key="tag" type="success" round size="medium">{{ tag }}</n-tag>
      </n-space>
      <n-text v-else depth="3">无标签</n-text>
    </n-card>

    <n-card class="section-card">
      <template #header>
        <n-space align="center">
          <span class="section-title">行动项</span>
          <n-tag size="small" round :type="data.action_items?.length ? 'warning' : 'default'">
            {{ data.action_items?.length || 0 }} 项
          </n-tag>
        </n-space>
      </template>

      <div v-if="data.action_items?.length" class="action-list">
        <div v-for="(item, index) in data.action_items" :key="item.id || index"
          class="action-item" :class="{ done: item.status === 'done', ignored: item.status === 'ignored' }">
          <n-space align="start" :size="12">
            <n-tag :type="priorityColor(item.priority)" size="small" round style="flex-shrink:0; margin-top:2px">
              {{ item.priority }}
            </n-tag>
            <span class="action-content">{{ item.content }}</span>
            <n-button v-if="item.status !== 'done'" size="tiny" type="success" ghost
              @click="toggleAction(item.id, 'done')">
              完成
            </n-button>
            <n-button v-if="item.status === 'pending'" size="tiny" type="warning" ghost
              @click="toggleAction(item.id, 'ignored')">
              忽略
            </n-button>
            <n-button v-if="item.status === 'ignored'" size="tiny" type="info" ghost
              @click="toggleAction(item.id, 'pending')">
              重开
            </n-button>
          </n-space>
        </div>
      </div>
      <n-empty v-else description="暂无行动项" />
    </n-card>

    <n-card v-if="data.raw_text" class="section-card">
      <template #header>
        <span class="section-title">原始内容</span>
      </template>
      <pre class="raw-text">{{ data.raw_text }}</pre>
    </n-card>

    <!-- 关联推荐 -->
    <n-card v-if="relatedItems.length" class="section-card">
      <template #header>
        <span class="section-title">关联推荐</span>
      </template>
      <n-list>
        <n-list-item v-for="item in relatedItems" :key="item.task_id" @click="$router.push(`/digest/${item.task_id}`)">
          <n-thing :title="item.title || '无标题'" :description="item.summary || '暂无摘要'">
            <template #avatar>
              <n-tag :type="statusType(item.status)" size="small">{{ statusLabel(item.status) }}</n-tag>
            </template>
          </n-thing>
        </n-list-item>
      </n-list>
    </n-card>

    <n-spin v-if="!data && !error" size="large" style="margin-top:40px" />
    <n-result v-if="error" status="error" title="加载失败" :description="error">
      <template #footer>
        <n-button @click="$router.push('/digest/list')">返回列表</n-button>
      </template>
    </n-result>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import api from '@/api'

const route = useRoute()
const message = useMessage()
const data = ref<any>(null)
const error = ref('')
const relatedItems = ref<any[]>([])

const taskId = ref(route.params.task_id as string)

function isSafeUrl(url: string | null | undefined): boolean {
  if (!url) return false
  const lower = url.toLowerCase().trim()
  return lower.startsWith('http://') || lower.startsWith('https://')
}

function statusType(status: string): 'success' | 'warning' | 'error' | 'default' {
  const map: Record<string, any> = { done: 'success', processing: 'warning', failed: 'error', parse_error: 'error' }
  return map[status] || 'default'
}

function statusLabel(status: string): string {
  const map: Record<string, string> = { done: '已完成', processing: '处理中', failed: '失败', parse_error: '解析错误' }
  return map[status] || status
}

function priorityColor(priority: string): 'error' | 'warning' | 'success' | 'default' {
  const map: Record<string, any> = { high: 'error', medium: 'warning', low: 'success' }
  return map[priority] || 'default'
}

function formatTime(iso: string): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return d.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return iso
  }
}

async function toggleAction(actionId: number, status: string) {
  try {
    await api.patch(`/actions/${actionId}`, { status })
    await fetchDetail()
  } catch (e: any) {
    console.error('Failed to update action:', e)
    message.error('更新行动项状态失败')
  }
}

async function fetchDetail() {
  error.value = ''
  if (!taskId.value) return
  try {
    const res: any = await api.get(`/digest/${taskId.value}`)
    data.value = res
    await fetchRelated(res.id)
  } catch (e: any) {
    error.value = e.message || '加载失败'
  }
}

async function fetchRelated(infoId: number) {
  try {
    const res: any = await api.get(`/digest/${taskId.value}/related`)
    relatedItems.value = (res.items || []).slice(0, 4)
  } catch (e) {
    console.error('Failed to load related items:', e)
  }
}

watch(() => route.params.task_id, (newId) => {
  taskId.value = newId as string
  fetchDetail()
})

onMounted(() => fetchDetail())
</script>

<style scoped>
.detail-header {
  margin-bottom: 20px;
}

.detail-header h2 {
  color: #cdd6f4;
  font-size: 18px;
}

.meta {
  font-size: 13px;
  color: #6c7086;
}

.source-link {
  color: #89b4fa;
  text-decoration: none;
}
.source-link:hover {
  text-decoration: underline;
}

.section-card {
  background: #1e1e2e;
  margin-bottom: 16px;
}

.section-title {
  font-weight: 600;
  color: #89b4fa;
}

.summary-text {
  color: #cdd6f4;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.action-item {
  padding: 8px 12px;
  border-radius: 6px;
  background: #181825;
  transition: opacity 0.2s;
}

.action-item.done {
  opacity: 0.5;
}

.action-item.done .action-content {
  text-decoration: line-through;
}

.action-item.ignored {
  opacity: 0.4;
}

.action-content {
  color: #cdd6f4;
  line-height: 1.6;
  flex: 1;
}

.raw-text {
  color: #a6adc8;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 400px;
  overflow-y: auto;
  font-family: inherit;
  font-size: 14px;
  margin: 0;
}
</style>
