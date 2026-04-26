<template>
  <div class="review-page">
    <h2>周复查复盘</h2>

    <n-spin :show="loading">
      <div v-if="stats && trends" class="review-content">
        <!-- 全局统计卡片 -->
        <n-space class="stats-row" size="large" align="stretch">
          <n-card class="stat-card">
            <n-statistic label="总知识卡片" :value="stats.total_info">
              <template #prefix>
                <n-icon :component="DocumentTextOutline" />
              </template>
            </n-statistic>
          </n-card>
          <n-card class="stat-card">
            <n-statistic label="总行动项" :value="stats.total_actions">
              <template #prefix>
                <n-icon :component="CheckmarkCircleOutline" />
              </template>
            </n-statistic>
          </n-card>
          <n-card class="stat-card">
            <n-statistic label="已完成" :value="stats.done_actions">
              <template #prefix>
                <n-icon :component="CheckmarkDoneOutline" />
              </template>
            </n-statistic>
          </n-card>
          <n-card class="stat-card">
            <n-statistic label="完成率" :value="((stats.completion_rate || 0) * 100).toFixed(1)" suffix="%">
              <template #prefix>
                <n-icon :component="TrendingUpOutline" />
              </template>
            </n-statistic>
          </n-card>
        </n-space>

        <n-divider />

        <!-- 图表区域 -->
        <n-grid :cols="2" :x-gap="16" :y-gap="16">
          <!-- 趋势图 -->
          <n-gi>
            <n-card title="近30天录入趋势">
              <v-chart :option="trendChartOption" :style="{ height: '350px' }" autoresize />
            </n-card>
          </n-gi>

          <!-- 标签分布 -->
          <n-gi>
            <n-card title="标签分布 Top 10">
              <v-chart v-if="trends.tag_distribution.length" :option="tagDistChartOption" :style="{ height: '350px' }" autoresize />
              <n-empty v-else description="暂无标签数据" />
            </n-card>
          </n-gi>
        </n-grid>

        <n-divider />

        <!-- 本周概览 -->
        <n-card title="本周概览">
          <n-space class="stats-row" size="large">
            <n-statistic label="本周新增信息" :value="weeklyData.new_info_count" />
            <n-statistic label="新增行动项" :value="weeklyData.new_action_count" />
            <n-statistic label="已完成" :value="weeklyData.done_action_count" />
            <n-statistic label="完成率" :value="((weeklyData.completion_rate || 0) * 100).toFixed(1)" suffix="%" />
          </n-space>
          <p style="margin-top: 12px; color: #a6adc8;">时间范围: {{ weeklyData.week_start }} ~ {{ weeklyData.week_end }}</p>
        </n-card>

        <n-divider />

        <!-- 待办行动项 -->
        <n-card v-if="weeklyData.pending_actions?.length" title="待办行动项">
          <n-list>
            <n-list-item v-for="(item, index) in weeklyData.pending_actions" :key="index">
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
import { ref, onMounted, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import {
  DocumentTextOutline,
  CheckmarkCircleOutline,
  CheckmarkDoneOutline,
  TrendingUpOutline,
} from '@vicons/ionicons5'
import api from '@/api'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
])

const message = useMessage()
const loading = ref(false)
const stats = ref<any>(null)
const trends = ref<any>(null)
const weeklyData = ref<any>(null)

function priorityType(priority: string): 'error' | 'warning' | 'default' {
  const map: Record<string, any> = { high: 'error', medium: 'warning', low: 'default' }
  return map[priority] || 'default'
}

// 趋势图配置
const trendChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(30, 30, 46, 0.9)',
    borderColor: '#45475a',
    textStyle: { color: '#cdd6f4' },
  },
  legend: {
    data: ['新增信息', '完成行动项'],
    textStyle: { color: '#a6adc8' },
    top: 0,
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true,
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: trends.value?.dates || [],
    axisLine: { lineStyle: { color: '#45475a' } },
    axisLabel: { color: '#a6adc8', fontSize: 11 },
  },
  yAxis: {
    type: 'value',
    axisLine: { lineStyle: { color: '#45475a' } },
    axisLabel: { color: '#a6adc8' },
    splitLine: { lineStyle: { color: '#313244' } },
  },
  series: [
    {
      name: '新增信息',
      type: 'line',
      smooth: true,
      data: trends.value?.info_counts || [],
      itemStyle: { color: '#89b4fa' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(137, 180, 250, 0.3)' },
            { offset: 1, color: 'rgba(137, 180, 250, 0.05)' },
          ],
        },
      },
    },
    {
      name: '完成行动项',
      type: 'line',
      smooth: true,
      data: trends.value?.done_counts || [],
      itemStyle: { color: '#a6e3a1' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(166, 227, 161, 0.3)' },
            { offset: 1, color: 'rgba(166, 227, 161, 0.05)' },
          ],
        },
      },
    },
  ],
}))

// 标签分布饼图配置
const tagDistChartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    backgroundColor: 'rgba(30, 30, 46, 0.9)',
    borderColor: '#45475a',
    textStyle: { color: '#cdd6f4' },
    formatter: '{b}: {c} ({d}%)',
  },
  legend: {
    orient: 'vertical',
    right: '5%',
    top: 'center',
    textStyle: { color: '#a6adc8' },
  },
  series: [
    {
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['40%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 8,
        borderColor: '#1e1e2e',
        borderWidth: 2,
      },
      label: {
        show: false,
        position: 'center',
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 16,
          fontWeight: 'bold',
          color: '#cdd6f4',
        },
      },
      labelLine: {
        show: false,
      },
      data: trends.value?.tag_distribution || [],
      color: ['#89b4fa', '#a6e3a1', '#f9e2af', '#fab387', '#f38ba8', '#cba6f7', '#94e2d5', '#89dceb', '#74c7ec', '#b4befe'],
    },
  ],
}))

async function fetchData() {
  loading.value = true
  try {
    const [statsRes, trendsRes, weeklyRes]: any[] = await Promise.all([
      api.get('/review/stats'),
      api.get('/review/monthly'),
      api.get('/review/weekly'),
    ])
    stats.value = statsRes
    trends.value = trendsRes
    weeklyData.value = weeklyRes
  } catch (e: any) {
    console.error('Failed to load review data:', e)
    message.error('加载数据失败，请稍后重试')
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

.stat-card :deep(.n-statistic .n-statistic-value) {
  font-size: 32px;
  font-weight: 600;
}

.stat-card :deep(.n-icon) {
  margin-right: 8px;
}
</style>
