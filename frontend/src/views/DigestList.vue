<template>
  <div class="digest-list">
    <h2>知识卡片</h2>

    <n-space class="filter-bar" align="center" :wrap="true">
      <n-input v-model:value="keyword" placeholder="搜索关键词" clearable style="width: 200px" @keyup.enter="fetchData" />
      <n-select v-model:value="statusFilter" :options="statusOptions" placeholder="状态筛选" clearable style="width: 150px"
        @update:value="onStatusChange" />
      <n-button type="primary" @click="fetchData">查询</n-button>
      <n-button :type="batchMode ? 'warning' : 'default'" @click="toggleBatchMode">
        {{ batchMode ? '退出批量管理' : '批量管理' }}
      </n-button>
      <n-dropdown :options="exportOptions" @select="handleExport">
        <n-button>导出</n-button>
      </n-dropdown>
    </n-space>

    <!-- 批量操作栏 -->
    <n-card v-if="batchMode && selectedIds.size > 0" class="batch-toolbar">
      <n-space align="center">
        <span>已选 {{ selectedIds.size }} 条</span>
        <n-button size="small" @click="selectAll">全选</n-button>
        <n-button size="small" @click="clearSelection">取消全选</n-button>
        <n-button size="small" type="error" @click="handleBatchDelete">批量删除</n-button>
        <n-button size="small" type="warning" @click="handleBatchArchive">批量归档</n-button>
        <n-button size="small" type="info" @click="showAddTagsModal = true">批量添加标签</n-button>
      </n-space>
    </n-card>

    <n-spin :show="loading">
      <div v-if="items.length" class="card-list">
        <n-card v-for="item in items" :key="item.id" hoverable class="info-card"
          @click="batchMode ? toggleSelect(item.id) : $router.push(`/digest/${item.task_id}`)">
          <template #header>
            <n-space justify="space-between" align="center">
              <n-space align="center">
                <n-checkbox v-if="batchMode" :checked="selectedIds.has(item.id)" @update:checked="toggleSelect(item.id)" />
                <span class="card-title">{{ item.title || '无标题' }}</span>
              </n-space>
              <n-tag :type="statusType(item.status)" size="small">{{ statusLabel(item.status) }}</n-tag>
            </n-space>
          </template>

          <p class="summary">{{ item.summary || '暂无摘要' }}</p>

          <template #footer>
            <n-space justify="space-between">
              <n-space>
                <n-tag v-for="tag in (item.tags || [])" :key="typeof tag === 'string' ? tag : tag.name || tag.id"
                  :type="isTagActive(typeof tag === 'string' ? tag : tag.name || tag) ? 'success' : 'info'" size="small"
                  round @click.stop="filterByTag(typeof tag === 'string' ? tag : tag.name || tag)">
                  {{ typeof tag === 'string' ? tag : tag.name || tag }}
                </n-tag>
              </n-space>
              <n-space align="center">
                <span class="meta">行动项: {{ item.action_count }}</span>
                <span class="meta">待办: {{ item.pending_action_count }}</span>
              </n-space>
            </n-space>
          </template>
        </n-card>
      </div>
      <n-empty v-else description="暂无数据" />
    </n-spin>

    <div v-if="total > pageSize" class="pagination">
      <n-pagination v-model:page="page" :page-count="Math.ceil(total / pageSize)" @update:page="fetchData" />
    </div>

    <!-- 批量添加标签弹窗 -->
    <n-modal v-model:show="showAddTagsModal" preset="dialog" title="批量添加标签">
      <n-space vertical>
        <p>选择要添加的标签:</p>
        <n-select v-model:value="selectedTagIds" :options="allTagOptions" multiple placeholder="选择标签" />
      </n-space>
      <template #action>
        <n-button @click="showAddTagsModal = false">取消</n-button>
        <n-button type="primary" @click="handleBatchAddTags">确定</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import api from '@/api'

const message = useMessage()
const dialog = useDialog()
const loading = ref(false)
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const statusFilter = ref<string | undefined>(undefined)
const tagFilter = ref('')

// 批量管理状态
const batchMode = ref(false)
const selectedIds = ref<Set<number>>(new Set())
const showAddTagsModal = ref(false)
const selectedTagIds = ref<number[]>([])
const allTagOptions = ref<{ label: string; value: number }[]>([])

const statusOptions: { label: string; value: string | undefined }[] = [
  { label: '全部', value: undefined },
  { label: '处理中', value: 'processing' },
  { label: '已完成', value: 'done' },
  { label: '已忽略', value: 'ignored' },
  { label: '失败', value: 'failed' },
]

function statusType(status: string): 'success' | 'warning' | 'error' | 'default' {
  const map: Record<string, any> = { done: 'success', processing: 'warning', failed: 'error', parse_error: 'error' }
  return map[status] || 'default'
}

function statusLabel(status: string): string {
  const map: Record<string, string> = { done: '已完成', processing: '处理中', failed: '失败', parse_error: '解析错误' }
  return map[status] || status
}

const exportOptions = [
  { label: '导出 Markdown', key: 'markdown' },
  { label: '导出 JSON', key: 'json' },
  { label: '导出 CSV', key: 'csv' },
]

async function handleExport(key: string) {
  try {
    const params: any = { format: key }
    if (statusFilter.value) params.status = statusFilter.value
    if (tagFilter.value) params.tags = tagFilter.value

    const res = await api.get('/export/digests', {
      params,
      responseType: 'blob',
    })

    const blob = new Blob([res])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const ext = key === 'markdown' ? 'md' : key
    link.download = `digests_export.${ext}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    message.success('导出成功')
  } catch (e: any) {
    message.error('导出失败')
  }
}

function onStatusChange() {
  page.value = 1
  fetchData()
}

function isTagActive(tagName: string): boolean {
  return tagFilter.value === tagName
}

function filterByTag(tagName: string) {
  if (tagFilter.value === tagName) {
    tagFilter.value = ''
  } else {
    tagFilter.value = tagName
  }
  page.value = 1
  fetchData()
}

function toggleBatchMode() {
  batchMode.value = !batchMode.value
  if (!batchMode.value) {
    selectedIds.value.clear()
  }
}

function toggleSelect(id: number) {
  if (selectedIds.value.has(id)) {
    selectedIds.value.delete(id)
  } else {
    selectedIds.value.add(id)
  }
}

function selectAll() {
  items.value.forEach(item => selectedIds.value.add(item.id))
}

function clearSelection() {
  selectedIds.value.clear()
}

async function handleBatchDelete() {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除选中的 ${selectedIds.value.size} 条知识卡片吗？此操作不可撤销。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const res: any = await api.delete('/digest/batch', { data: { ids: Array.from(selectedIds.value) } })
        message.success(`已删除 ${res.deleted_count} 条知识卡片`)
        selectedIds.value.clear()
        await fetchData()
      } catch (e: any) {
        message.error(e.response?.data?.message || '删除失败')
      }
    },
  })
}

async function handleBatchArchive() {
  try {
    const res: any = await api.patch('/digest/batch/status', {
      ids: Array.from(selectedIds.value),
      status: 'archived',
    })
    message.success(`已归档 ${res.updated_count} 条知识卡片`)
    selectedIds.value.clear()
    await fetchData()
  } catch (e: any) {
    message.error(e.response?.data?.message || '归档失败')
  }
}

async function handleBatchAddTags() {
  if (selectedTagIds.value.length === 0) {
    message.warning('请至少选择一个标签')
    return
  }

  try {
    const res: any = await api.post('/digest/batch/tags', {
      ids: Array.from(selectedIds.value),
      tag_ids: selectedTagIds.value,
    })
    message.success(`已为 ${res.updated_count} 条知识卡片添加标签`)
    showAddTagsModal.value = false
    selectedTagIds.value = []
    await fetchData()
  } catch (e: any) {
    message.error(e.response?.data?.message || '添加标签失败')
  }
}

async function fetchTags() {
  try {
    const res: any = await api.get('/tags', { params: { page_size: 100 } })
    allTagOptions.value = (res.items || []).map((tag: any) => ({
      label: tag.name,
      value: tag.id,
    }))
  } catch (e) {
    console.error('Failed to load tags:', e)
  }
}

async function fetchData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (keyword.value) params.keyword = keyword.value
    if (statusFilter.value) params.status = statusFilter.value
    if (tagFilter.value) params.tags = tagFilter.value

    const res: any = await api.get('/digest', { params })
    items.value = res.items || []
    total.value = res.total || 0
  } catch (e: any) {
    console.error('Failed to load digest list:', e)
    message.error('加载知识卡片失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
  fetchTags()
})
</script>

<style scoped>
.digest-list h2 {
  margin-bottom: 20px;
  color: #89b4fa;
}

.filter-bar {
  margin-bottom: 16px;
}

.batch-toolbar {
  margin-bottom: 16px;
  background: #313244;
  border: 1px solid #45475a;
}

.card-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-card {
  background: #1e1e2e;
  cursor: pointer;
  transition: all 0.2s ease;
}

.info-card:hover {
  border-color: #89b4fa;
}

.card-title {
  font-weight: 600;
  color: #cdd6f4;
}

.summary {
  color: #a6adc8;
  line-height: 1.6;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.meta {
  font-size: 12px;
  color: #6c7086;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
