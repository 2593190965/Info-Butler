<template>
  <div class="actions-page">
    <h2>行动项看板</h2>

    <n-space class="filter-bar" align="center">
      <n-select
        v-model:value="priorityFilter"
        :options="priorityOptions"
        placeholder="优先级筛选"
        clearable
        style="width: 150px"
      />
    </n-space>

    <div class="kanban">
      <div v-for="col in columns" :key="col.key" class="kanban-column">
        <div class="column-header" :style="{ borderColor: col.color }">
          <span>{{ col.label }}</span>
          <n-badge :value="getItems(col.key).length" :max="99" type="info" />
        </div>
        <div class="column-body">
          <n-card
            v-for="item in getItems(col.key)"
            :key="item.id"
            hoverable
            size="small"
            class="action-card"
          >
            <p>{{ item.content }}</p>
            <template #footer>
              <n-space justify="space-between">
                <n-tag :type="priorityType(item.priority)" size="small" round>
                  {{ item.priority }}
                </n-tag>
                <n-space>
                  <n-button
                    v-if="col.key !== 'done'"
                    size="tiny"
                    type="success"
                    @click="updateStatus(item.id, 'done')"
                  >
                    完成
                  </n-button>
                  <n-button
                    v-if="col.key !== 'ignored'"
                    size="tiny"
                    type="warning"
                    @click="updateStatus(item.id, 'ignored')"
                  >
                    忽略
                  </n-button>
                  <n-button
                    v-if="col.key === 'done' || col.key === 'ignored'"
                    size="tiny"
                    @click="updateStatus(item.id, 'pending')"
                  >
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useMessage } from 'naive-ui'
import api from '@/api'

const message = useMessage()
const loading = ref(false)
const items = ref<any[]>([])
const priorityFilter = ref<string | null>(null)

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

async function fetchData() {
  loading.value = true
  try {
    const params: any = {}
    if (priorityFilter.value) params.priority = priorityFilter.value

    const res: any = await api.get('/actions', { params })
    items.value = res.items || []
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
</style>
