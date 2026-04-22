<template>
  <div class="digest-list">
    <h2>知识卡片</h2>

    <n-space class="filter-bar" align="center" :wrap="true">
      <n-input v-model:value="keyword" placeholder="搜索关键词" clearable style="width: 200px" />
      <n-select v-model:value="statusFilter" :options="statusOptions" placeholder="状态筛选" clearable
        style="width: 150px" />
      <n-button type="primary" @click="fetchData">查询</n-button>
    </n-space>

    <n-spin :show="loading">
      <div v-if="items.length" class="card-list">
        <n-card v-for="item in items" :key="item.id" hoverable class="info-card" @click="$router.push(`/digest/${item.task_id}`)">
          <template #header>
            <n-space justify="space-between" align="center">
              <span class="card-title">{{ item.title || '无标题' }}</span>
              <n-tag :type="statusType(item.status)" size="small">{{ statusLabel(item.status) }}</n-tag>
            </n-space>
          </template>

          <p class="summary">{{ item.summary || '暂无摘要' }}</p>

          <template #footer>
            <n-space justify="space-between">
              <n-space>
                <n-tag v-for="tag in (item.tags || [])"
                  :key="typeof tag === 'string' ? tag : tag.name || tag.id" size="small" round type="info"
                  @click.stop="filterByTag(typeof tag === 'string' ? tag : tag.name || tag)">
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/api'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const statusFilter = ref<string | null>(null)

const statusOptions = [
  { label: '已完成', value: 'done' },
  { label: '处理中', value: 'processing' },
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

function filterByTag(tagName: string) {
  keyword.value = tagName
  fetchData()
}

async function fetchData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (keyword.value) params.keyword = keyword.value
    if (statusFilter.value) params.status = statusFilter.value

    const res: any = await api.get('/digest', { params })
    items.value = res.items || []
    total.value = res.total || 0
  } catch (e: any) {
    console.error('Failed to load digest list:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => fetchData())
</script>

<style scoped>
.digest-list h2 {
  margin-bottom: 20px;
  color: #89b4fa;
}

.filter-bar {
  margin-bottom: 16px;
}

.card-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-card {
  background: #1e1e2e;
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
