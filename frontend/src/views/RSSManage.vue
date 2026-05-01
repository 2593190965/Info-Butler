<template>
  <div class="rss-manage">
    <div class="header">
      <h2>RSS 订阅管理</h2>
      <n-button type="primary" @click="showAddModal = true">添加订阅</n-button>
    </div>

    <n-spin :show="loading">
      <n-empty v-if="!subscriptions.length && !loading" description="暂无 RSS 订阅" />

      <n-grid v-else :cols="2" :x-gap="16" :y-gap="16">
        <n-gi v-for="sub in subscriptions" :key="sub.id">
          <n-card :title="sub.name" size="small">
            <template #header-extra>
              <n-tag :type="sub.enabled ? 'success' : 'default'" round>
                {{ sub.enabled ? '启用' : '禁用' }}
              </n-tag>
            </template>

            <n-descriptions :column="1" size="small" bordered>
              <n-descriptions-item label="URL">
                <n-ellipsis :line-clamp="1">{{ sub.url }}</n-ellipsis>
              </n-descriptions-item>
              <n-descriptions-item label="抓取间隔">{{ formatInterval(sub.fetch_interval) }}</n-descriptions-item>
              <n-descriptions-item label="文章数">{{ sub.article_count }}</n-descriptions-item>
              <n-descriptions-item label="最后抓取">
                {{ sub.last_fetch_at ? formatTime(sub.last_fetch_at) : '从未' }}
              </n-descriptions-item>
              <n-descriptions-item label="状态">
                <n-tag v-if="sub.last_fetch_status" :type="sub.last_fetch_status === 'success' ? 'success' : 'error'"
                  size="small">
                  {{ sub.last_fetch_status === 'success' ? '成功' : '失败' }}
                </n-tag>
                <span v-else>-</span>
              </n-descriptions-item>
            </n-descriptions>

            <template #action>
              <n-space>
                <n-button size="small" @click="handleFetch(sub)">立即抓取</n-button>
                <n-button size="small" @click="handleEdit(sub)">编辑</n-button>
                <n-button size="small" type="error" @click="handleDelete(sub)">删除</n-button>
              </n-space>
            </template>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>

    <n-modal v-model:show="showAddModal" preset="dialog" :title="editingSub ? '编辑订阅' : '添加订阅'">
      <n-form :model="form" :rules="rules" label-placement="left" label-width="80">
        <n-form-item label="名称" path="name">
          <n-input v-model:value="form.name" placeholder="订阅名称" />
        </n-form-item>
        <n-form-item label="URL" path="url">
          <n-input v-model:value="form.url" placeholder="https://example.com/rss" />
        </n-form-item>
        <n-form-item label="抓取间隔" path="fetch_interval">
          <n-select v-model:value="form.fetch_interval" :options="intervalOptions" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showAddModal = false">取消</n-button>
          <n-button type="primary" @click="handleSubmit" :loading="submitting">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import api from '@/api'

const message = useMessage()
const dialog = useDialog()
const loading = ref(false)
const submitting = ref(false)
const showAddModal = ref(false)
const editingSub = ref<any>(null)
const subscriptions = ref<any[]>([])

const form = reactive({
  name: '',
  url: '',
  fetch_interval: 3600,
})

const rules = {
  name: { required: true, message: '请输入订阅名称', trigger: 'blur' },
  url: { required: true, message: '请输入 RSS URL', trigger: 'blur' },
}

const intervalOptions = [
  { label: '每 5 分钟', value: 300 },
  { label: '每 15 分钟', value: 900 },
  { label: '每 30 分钟', value: 1800 },
  { label: '每 1 小时', value: 3600 },
  { label: '每 6 小时', value: 21600 },
  { label: '每 12 小时', value: 43200 },
  { label: '每 24 小时', value: 86400 },
]

function formatInterval(seconds: number): string {
  if (seconds < 3600) return `${seconds / 60} 分钟`
  if (seconds < 86400) return `${seconds / 3600} 小时`
  return `${seconds / 86400} 天`
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('zh-CN')
}

async function loadSubscriptions() {
  loading.value = true
  try {
    subscriptions.value = await api.get('/rss')
  } catch (e: any) {
    message.error('加载订阅列表失败')
  } finally {
    loading.value = false
  }
}

function handleEdit(sub: any) {
  editingSub.value = sub
  form.name = sub.name
  form.url = sub.url
  form.fetch_interval = sub.fetch_interval
  showAddModal.value = true
}

async function handleSubmit() {
  submitting.value = true
  try {
    if (editingSub.value) {
      await api.put(`/rss/${editingSub.value.id}`, form)
      message.success('更新成功')
    } else {
      await api.post('/rss', form)
      message.success('添加成功')
    }
    showAddModal.value = false
    resetForm()
    await loadSubscriptions()
  } catch (e: any) {
    message.error(e.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  form.name = ''
  form.url = ''
  form.fetch_interval = 3600
  editingSub.value = null
}

function handleFetch(sub: any) {
  dialog.info({
    title: '确认',
    content: `立即抓取 "${sub.name}" 的最新文章？`,
    positiveText: '确认',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const result: any = await api.post(`/rss/${sub.id}/fetch`)
        message.success(`抓取完成：获取 ${result.fetched} 篇，新增 ${result.new} 篇`)
        await loadSubscriptions()
      } catch (e: any) {
        message.error('抓取失败')
      }
    },
  })
}

function handleDelete(sub: any) {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除订阅 "${sub.name}" 吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await api.delete(`/rss/${sub.id}`)
        message.success('删除成功')
        await loadSubscriptions()
      } catch (e: any) {
        message.error('删除失败')
      }
    },
  })
}

onMounted(loadSubscriptions)
</script>

<style scoped>
.rss-manage .header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.rss-manage h2 {
  margin: 0;
  color: #89b4fa;
}
</style>
