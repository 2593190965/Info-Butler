<template>
  <div class="review-page">
    <h2>周报复盘</h2>

    <n-spin :show="loading">
      <div v-if="data" class="review-content">
        <n-space class="stats-row" size="large" align="stretch">
          <n-card class="stat-card">
            <n-statistic label="本周新增信息" :value="data.new_info_count" />
          </n-card>
          <n-card class="stat-card">
            <n-statistic label="新增行动项" :value="data.new_action_count" />
          </n-card>
          <n-card class="stat-card">
            <n-statistic label="已完成" :value="data.done_action_count" />
          </n-card>
          <n-card class="stat-card">
            <n-statistic label="完成率" :value="((data.completion_rate || 0) * 100).toFixed(1)" suffix="%" />
          </n-card>
        </n-space>

        <n-divider />

        <n-card title="时间范围">
          <p>{{ data.week_start }} ~ {{ data.week_end }}</p>
        </n-card>

        <n-divider />

        <n-card v-if="data.pending_actions?.length" title="待办行动项">
          <n-list>
            <n-list-item v-for="(item, index) in data.pending_actions" :key="index">
              <template #prefix>
                <n-tag :type="priorityType(item.priority)" size="small" round>
                  {{ item.priority }}
                </n-tag>
              </template>
              {{ item.content }}
              <template #suffix>
                <n-button size="tiny" type="success" @click="completeAction(item.id)">
                  完成
                </n-button>
              </template>
            </n-list-item>
          </n-list>
        </n-card>

        <n-card v-else title="待办行动项">
          <n-empty description="暂无待办事项，太棒了！" />
        </n-card>
      </div>
      <n-empty v-else description="加载中..." />
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import api from '@/api'

const message = useMessage()
const loading = ref(false)
const data = ref<any>(null)

function priorityType(priority: string): 'error' | 'warning' | 'default' {
  const map: Record<string, any> = { high: 'error', medium: 'warning', low: 'default' }
  return map[priority] || 'default'
}

async function fetchData() {
  loading.value = true
  try {
    const res: any = await api.get('/review/weekly')
    data.value = res
  } catch (e: any) {
    console.error('Failed to load review data:', e)
    message.error('加载周报数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function completeAction(id: number) {
  try {
    await api.patch(`/actions/${id}`, { status: 'done' })
    message.success('已完成')
    await fetchData()
  } catch (e: any) {
    message.error(e.response?.data?.message || '操作失败')
  }
}

onMounted(() => fetchData())
</script>

<style scoped>
.review-page h2 {
  margin-bottom: 20px;
  color: #89b4fa;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: #181825;
  text-align: center;
}
</style>
