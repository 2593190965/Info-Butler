<template>
  <div class="actions-page">
    <h2>行动项看板</h2>

    <n-space class="filter-bar" align="center">
      <n-select v-model:value="priorityFilter" :options="priorityOptions" placeholder="优先级筛选" clearable
        style="width: 150px" />
      <n-button :type="batchMode ? 'warning' : 'default'" @click="toggleBatchMode">
        {{ batchMode ? '退出批量管理' : '批量管理' }}
      </n-button>
    </n-space>

    <!-- 批量操作栏 -->
    <n-card v-if="batchMode && selectedIds.size > 0" class="batch-toolbar">
      <n-space align="center">
        <span>已选 {{ selectedIds.size }} 条</span>
        <n-button size="small" @click="selectAll">全选</n-button>
        <n-button size="small" @click="clearSelection">取消全选</n-button>
        <n-button size="small" type="error" @click="handleBatchDelete">批量删除</n-button>
        <n-dropdown :options="batchStatusOptions" @select="handleBatchStatus">
          <n-button size="small">批量修改状态</n-button>
        </n-dropdown>
        <n-dropdown :options="batchPriorityOptions" @select="handleBatchPriority">
          <n-button size="small">批量修改优先级</n-button>
        </n-dropdown>
        <n-button size="small" type="info" @click="showAddTagsModal = true">批量添加标签</n-button>
      </n-space>
    </n-card>

    <div class="kanban">
      <div v-for="col in columns" :key="col.key" class="kanban-column">
        <div class="column-header" :style="{ borderColor: col.color }">
          <span>{{ col.label }}</span>
          <n-badge :value="getItems(col.key).length" :max="99" type="info" />
        </div>
        <div class="column-body">
          <n-card v-for="item in getItems(col.key)" :key="item.id" hoverable size="small"
            :class="['action-card', getDueClass(item)]" @click="batchMode ? toggleSelect(item.id) : null">
            <template #header v-if="batchMode">
              <n-checkbox :checked="selectedIds.has(item.id)" @update:checked="toggleSelect(item.id)" />
            </template>
            <p>{{ item.content }}</p>
            <div v-if="item.due_date" class="due-info">
              <n-tag :type="getDueTagType(item)" size="tiny" round>
                {{ formatDueDate(item) }}
              </n-tag>
            </div>
            <template #footer>
              <n-space justify="space-between">
                <n-tag :type="priorityType(item.priority)" size="small" round>
                  {{ item.priority }}
                </n-tag>
                <n-space v-if="!batchMode">
                  <n-button size="tiny" type="primary" @click="openEditModal(item)">
                    编辑
                  </n-button>
                  <n-button v-if="col.key !== 'done'" size="tiny" type="success" @click="updateStatus(item.id, 'done')">
                    完成
                  </n-button>
                  <n-button v-if="col.key !== 'ignored'" size="tiny" type="warning"
                    @click="updateStatus(item.id, 'ignored')">
                    忽略
                  </n-button>
                  <n-button v-if="col.key === 'done' || col.key === 'ignored'" size="tiny"
                    @click="updateStatus(item.id, 'pending')">
                    重开
                  </n-button>
                </n-space>
              </n-space>
            </template>
          </n-card>
          <n-empty v-if="!getItems(col.key).length" description="暂无" size="small" />
        </div>
      </div>
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

    <!-- 编辑行动项弹窗 -->
    <n-modal v-model:show="showEditModal" preset="dialog" title="编辑行动项">
      <n-space vertical>
        <n-form-item label="内容">
          <n-input v-model:value="editForm.content" type="textarea" placeholder="行动项内容" :rows="3" />
        </n-form-item>
        <n-form-item label="优先级">
          <n-select v-model:value="editForm.priority" :options="priorityOptions" placeholder="选择优先级" />
        </n-form-item>
        <n-form-item label="截止日期">
          <n-date-picker v-model:value="editForm.dueDateTimestamp" type="date" clearable />
        </n-form-item>
      </n-space>
      <template #action>
        <n-button @click="showEditModal = false">取消</n-button>
        <n-button type="primary" @click="handleEdit">保存</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import api from '@/api'

const message = useMessage()
const dialog = useDialog()
const loading = ref(false)
const items = ref<any[]>([])
const priorityFilter = ref<string | null>(null)

// 批量管理
const batchMode = ref(false)
const selectedIds = ref(new Set<number>())
const showAddTagsModal = ref(false)
const selectedTagIds = ref<number[]>([])
const allTags = ref<any[]>([])

// 编辑功能
const showEditModal = ref(false)
const editForm = ref({
  id: 0,
  content: '',
  priority: 'medium',
  dueDateTimestamp: null as number | null,
})

const columns = [
  { key: 'pending', label: '待办', color: '#f9e2af' },
  { key: 'done', label: '已完成', color: '#a6e3a1' },
  { key: 'ignored', label: '已忽略', color: '#f38ba8' },
]

const priorityOptions = [
  { label: '高', value: 'high' },
  { label: '中', value: 'medium' },
  { label: '低', value: 'low' },
]

const batchStatusOptions = [
  { label: '标记为待办', key: 'pending' },
  { label: '标记为完成', key: 'done' },
  { label: '标记为忽略', key: 'ignored' },
]

const batchPriorityOptions = [
  { label: '高', key: 'high' },
  { label: '中', key: 'medium' },
  { label: '低', key: 'low' },
]

const allTagOptions = computed(() => allTags.value.map((t) => ({ label: t.name, value: t.id })))

function getItems(status: string) {
  let filtered = items.value.filter((i) => i.status === status)
  if (priorityFilter.value) {
    filtered = filtered.filter((i) => i.priority === priorityFilter.value)
  }
  return filtered
}

function priorityType(priority: string): 'error' | 'warning' | 'default' {
  const map: Record<string, any> = { high: 'error', medium: 'warning', low: 'default' }
  return map[priority] || 'default'
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
  selectedIds.value = new Set(selectedIds.value)
}

function selectAll() {
  items.value.forEach((item) => selectedIds.value.add(item.id))
  selectedIds.value = new Set(selectedIds.value)
}

function clearSelection() {
  selectedIds.value.clear()
  selectedIds.value = new Set(selectedIds.value)
}

function getDueClass(item: any): string {
  if (!item.due_date || item.status !== 'pending') return ''
  const due = new Date(item.due_date)
  const now = new Date()
  const diff = (due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
  if (diff < 0) return 'overdue'
  if (diff <= 1) return 'due-soon'
  return ''
}

function getDueTagType(item: any): 'error' | 'warning' | 'default' {
  if (!item.due_date) return 'default'
  const due = new Date(item.due_date)
  const now = new Date()
  const diff = (due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
  if (diff < 0) return 'error'
  if (diff <= 1) return 'warning'
  return 'default'
}

function formatDueDate(item: any): string {
  if (!item.due_date) return ''
  const due = new Date(item.due_date)
  const now = new Date()
  const diff = Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
  if (diff < 0) return `逾期 ${Math.abs(diff)} 天`
  if (diff === 0) return '今天到期'
  if (diff === 1) return '明天到期'
  return `${diff} 天后到期`
}

async function fetchData() {
  loading.value = true
  try {
    const params: any = {}
    if (priorityFilter.value) params.priority = priorityFilter.value

    const [res, tagsRes]: any[] = await Promise.all([
      api.get('/actions', { params }),
      api.get('/tags'),
    ])
    items.value = res.items || []
    allTags.value = tagsRes || []
  } catch (e: any) {
    console.error('Failed to load actions:', e)
    message.error('加载行动项失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function updateStatus(id: number, status: string) {
  try {
    await api.patch(`/actions/${id}`, { status })
    message.success('已更新')
    await fetchData()
  } catch (e: any) {
    message.error(e.response?.data?.message || '更新失败')
  }
}

async function handleBatchDelete() {
  if (selectedIds.value.size === 0) return
  dialog.warning({
    title: '确认删除',
    content: `确定要删除选中的 ${selectedIds.value.size} 条行动项吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await api.delete('/actions/batch', { data: { ids: [...selectedIds.value] } })
        message.success('已批量删除')
        selectedIds.value.clear()
        await fetchData()
      } catch (e: any) {
        message.error(e.response?.data?.message || '删除失败')
      }
    },
  })
}

async function handleBatchStatus(key: string) {
  if (selectedIds.value.size === 0) return
  try {
    await api.patch('/actions/batch/status', { ids: [...selectedIds.value], status: key })
    message.success('已批量更新状态')
    selectedIds.value.clear()
    await fetchData()
  } catch (e: any) {
    message.error(e.response?.data?.message || '更新失败')
  }
}

async function handleBatchPriority(key: string) {
  if (selectedIds.value.size === 0) return
  try {
    await api.patch('/actions/batch/priority', { ids: [...selectedIds.value], priority: key })
    message.success('已批量更新优先级')
    selectedIds.value.clear()
    await fetchData()
  } catch (e: any) {
    message.error(e.response?.data?.message || '更新失败')
  }
}

async function handleBatchAddTags() {
  if (selectedIds.value.size === 0 || selectedTagIds.value.length === 0) return
  try {
    await api.post('/actions/batch/tags', { ids: [...selectedIds.value], tag_ids: selectedTagIds.value })
    message.success('已批量添加标签')
    selectedIds.value.clear()
    selectedTagIds.value = []
    showAddTagsModal.value = false
    await fetchData()
  } catch (e: any) {
    message.error(e.response?.data?.message || '添加标签失败')
  }
}

function openEditModal(item: any) {
  editForm.value = {
    id: item.id,
    content: item.content,
    priority: item.priority,
    dueDateTimestamp: item.due_date ? new Date(item.due_date).getTime() : null,
  }
  showEditModal.value = true
}

async function handleEdit() {
  if (!editForm.value.content.trim()) {
    message.error('内容不能为空')
    return
  }
  try {
    const updateData: any = {
      content: editForm.value.content,
      priority: editForm.value.priority,
    }
    if (editForm.value.dueDateTimestamp) {
      const date = new Date(editForm.value.dueDateTimestamp)
      updateData.due_date = date.toISOString().split('T')[0]
    }

    await api.patch(`/actions/${editForm.value.id}`, updateData)
    message.success('已更新')
    showEditModal.value = false
    await fetchData()
  } catch (e: any) {
    message.error(e.response?.data?.message || '更新失败')
  }
}

onMounted(() => fetchData())
</script>

<style scoped>
.actions-page h2 {
  margin-bottom: 20px;
  color: #89b4fa;
}

.filter-bar {
  margin-bottom: 16px;
}

.kanban {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.kanban-column {
  background: #181825;
  border-radius: 8px;
  padding: 12px;
  min-height: 400px;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  margin-bottom: 12px;
  border-bottom: 2px solid;
  font-weight: 600;
  color: #cdd6f4;
}

.column-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-card {
  background: #1e1e2e;
}

.action-card p {
  font-size: 14px;
  line-height: 1.5;
  color: #cdd6f4;
}

.batch-toolbar {
  margin-bottom: 16px;
  background: #1e1e2e;
  border: 1px solid #45475a;
}

.action-card {
  cursor: default;
}

.action-card:has(.n-checkbox) {
  cursor: pointer;
}

.action-card.overdue {
  border: 1px solid #f38ba8;
  animation: pulse-border 2s ease-in-out infinite;
}

.action-card.due-soon {
  border: 1px solid #f9e2af;
}

@keyframes pulse-border {

  0%,
  100% {
    border-color: #f38ba8;
  }

  50% {
    border-color: #585b70;
  }
}

.due-info {
  margin-bottom: 8px;
}
</style>
