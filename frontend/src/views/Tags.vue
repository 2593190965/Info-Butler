<template>
  <div class="tags-page">
    <h2>标签管理</h2>

    <n-space class="action-bar" align="center">
      <n-input v-model:value="keyword" placeholder="搜索标签" clearable style="width: 200px" @keyup.enter="fetchData">
        <template #prefix>
          <n-icon><SearchOutline /></n-icon>
        </template>
      </n-input>
      <n-button type="primary" @click="openCreateModal">新建标签</n-button>
    </n-space>

    <n-spin :show="loading">
      <div v-if="items.length" class="tag-list">
        <n-card v-for="item in items" :key="item.id" hoverable size="small" class="tag-card">
          <template #header>
            <n-space justify="space-between" align="center">
              <span class="tag-name">{{ item.name }}</span>
              <n-space align="center" :size="4">
                <n-tag size="tiny" round type="info">{{ item.info_count || 0 }} 信息</n-tag>
                <n-tag size="tiny" round type="warning">{{ item.action_count || 0 }} 行动项</n-tag>
              </n-space>
            </n-space>
          </template>

          <n-space justify="end" :size="8">
            <n-button size="small" @click="openEditModal(item)">编辑</n-button>
            <n-button size="small" type="error" ghost @click="handleDelete(item.id, item.name)">删除</n-button>
          </n-space>
        </n-card>
      </div>
      <n-empty v-else description="暂无标签" />
    </n-spin>

    <div v-if="total > pageSize" class="pagination">
      <n-pagination v-model:page="page" :page-count="Math.ceil(total / pageSize)" @update:page="fetchData" />
    </div>

    <n-modal v-model:show="showModal" preset="dialog" :title="isEdit ? '编辑标签' : '新建标签'" positive-text="保存"
      negative-text="取消" @positive-click="handleSubmit">
      <n-form ref="formRef" :model="form" :rules="rules">
        <n-form-item label="标签名称" path="name">
          <n-input v-model:value="form.name" placeholder="输入标签名称（2-20字符）" maxlength="20" show-count />
        </n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { SearchOutline } from '@vicons/ionicons5'
import api from '@/api'

const message = useMessage()
const loading = ref(false)
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const keyword = ref('')

const showModal = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const formRef = ref<any>(null)

const form = reactive({ name: '' })

const rules = {
  name: [
    { required: true, message: '请输入标签名称', trigger: 'blur' },
    { min: 2, max: 20, message: '长度在 2-20 个字符', trigger: 'blur' },
  ],
}

function resetForm() {
  form.name = ''
  isEdit.value = false
  editId.value = null
}

function openCreateModal() {
  resetForm()
  showModal.value = true
}

function openEditModal(item: any) {
  resetForm()
  isEdit.value = true
  editId.value = item.id
  form.name = item.name
  showModal.value = true
}

async function handleSubmit() {
  try {
    if (isEdit.value && editId.value) {
      await api.put(`/tags/${editId.value}`, { name: form.name })
      message.success('标签已更新')
    } else {
      await api.post('/tags', { name: form.name })
      message.success('标签已创建')
    }
    showModal.value = false
    fetchData()
  } catch (e: any) {
    message.error(e.message || '操作失败')
  }
}

async function handleDelete(id: number, name: string) {
  try {
    await api.delete(`/tags/${id}`)
    message.success(`"${name}" 已删除`)
    fetchData()
  } catch (e: any) {
    message.error(e.message || '删除失败')
  }
}

async function fetchData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (keyword.value) params.keyword = keyword.value

    const res: any = await api.get('/tags', { params })
    items.value = res.items || []
    total.value = res.total || 0
  } catch (e: any) {
    console.error('Failed to load tags:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => fetchData())
</script>

<style scoped>
.tags-page h2 {
  margin-bottom: 20px;
  color: #89b4fa;
}

.action-bar {
  margin-bottom: 16px;
}

.tag-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 12px;
}

.tag-card {
  background: #1e1e2e;
}

.tag-name {
  font-weight: 500;
  color: #cdd6f4;
  font-size: 15px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
