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
      <n-button :type="batchMode ? 'warning' : 'default'" @click="toggleBatchMode">
        {{ batchMode ? '退出批量管理' : '批量管理' }}
      </n-button>
    </n-space>

    <!-- 批量操作栏 -->
    <n-card v-if="batchMode && selectedIds.size > 0" class="batch-toolbar">
      <n-space align="center">
        <span>已选 {{ selectedIds.size }} 个</span>
        <n-button size="small" @click="selectAll">全选</n-button>
        <n-button size="small" @click="clearSelection">取消全选</n-button>
        <n-button size="small" type="error" @click="handleBatchDelete">批量删除</n-button>
        <n-button size="small" type="info" @click="showMergeModal = true">合并标签</n-button>
      </n-space>
    </n-card>

    <n-spin :show="loading">
      <div v-if="items.length" class="tag-list">
        <n-card v-for="item in items" :key="item.id" hoverable size="small" class="tag-card"
          @click="batchMode ? toggleSelect(item.id) : null">
          <template #header>
            <n-space justify="space-between" align="center">
              <n-space align="center" :size="8">
                <n-checkbox v-if="batchMode" :checked="selectedIds.has(item.id)"
                  @update:checked="toggleSelect(item.id)" @click.stop />
                <span class="tag-name">{{ item.name }}</span>
              </n-space>
              <n-space align="center" :size="4">
                <n-tag size="tiny" round type="info">{{ item.info_count || 0 }} 信息</n-tag>
                <n-tag size="tiny" round type="warning">{{ item.action_count || 0 }} 行动项</n-tag>
              </n-space>
            </n-space>
          </template>

          <n-space justify="end" :size="8">
            <n-button v-if="!batchMode" size="small" @click="openEditModal(item)">编辑</n-button>
            <n-button v-if="!batchMode" size="small" type="error" ghost
              @click="handleDelete(item.id, item.name)">删除</n-button>
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

    <!-- 合并标签弹窗 -->
    <n-modal v-model:show="showMergeModal" preset="dialog" title="合并标签">
      <n-space vertical>
        <p>将选中的标签合并到目标标签：</p>
        <n-select v-model:value="mergeTargetId" :options="mergeTargetOptions" placeholder="选择目标标签" clearable />
        <n-divider>或创建新标签</n-divider>
        <n-input v-model:value="mergeNewName" placeholder="输入新标签名称" />
      </n-space>
      <template #action>
        <n-button @click="showMergeModal = false">取消</n-button>
        <n-button type="primary" @click="handleMerge">确定</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import { SearchOutline } from '@vicons/ionicons5'
import api from '@/api'

const message = useMessage()
const dialog = useDialog()
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

// 批量管理
const batchMode = ref(false)
const selectedIds = ref(new Set<number>())
const showMergeModal = ref(false)
const mergeTargetId = ref<number | null>(null)
const mergeNewName = ref('')

const rules = {
  name: [
    { required: true, message: '请输入标签名称', trigger: 'blur' },
    { min: 2, max: 20, message: '长度在 2-20 个字符', trigger: 'blur' },
  ],
}

const mergeTargetOptions = computed(() =>
  items.value
    .filter((t) => !selectedIds.value.has(t.id))
    .map((t) => ({ label: t.name, value: t.id }))
)

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

async function handleBatchDelete() {
  if (selectedIds.value.size === 0) return
  dialog.warning({
    title: '确认删除',
    content: `确定要删除选中的 ${selectedIds.value.size} 个标签吗？关联的信息和行动项不会被删除。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await api.delete('/tags/batch', { data: { ids: [...selectedIds.value] } })
        message.success('已批量删除')
        selectedIds.value.clear()
        await fetchData()
      } catch (e: any) {
        message.error(e.response?.data?.message || '删除失败')
      }
    },
  })
}

async function handleMerge() {
  if (selectedIds.value.size === 0) return

  const sourceIds = [...selectedIds.value]

  if (mergeTargetId.value) {
    if (sourceIds.includes(mergeTargetId.value)) {
      message.error('目标标签不能是选中的标签之一')
      return
    }
    try {
      await api.post('/tags/merge', { source_ids: sourceIds, target_id: mergeTargetId.value })
      message.success('标签已合并')
      selectedIds.value.clear()
      mergeTargetId.value = null
      showMergeModal.value = false
      await fetchData()
    } catch (e: any) {
      message.error(e.response?.data?.message || '合并失败')
    }
  } else if (mergeNewName.value.trim()) {
    try {
      const createRes: any = await api.post('/tags', { name: mergeNewName.value.trim() })
      const targetId = createRes.id
      await api.post('/tags/merge', { source_ids: sourceIds, target_id: targetId })
      message.success('标签已合并到新标签')
      selectedIds.value.clear()
      mergeNewName.value = ''
      showMergeModal.value = false
      await fetchData()
    } catch (e: any) {
      message.error(e.response?.data?.message || '合并失败')
    }
  } else {
    message.error('请选择目标标签或输入新标签名称')
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
    message.error('加载标签失败，请稍后重试')
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

.batch-toolbar {
  margin-bottom: 16px;
  background: #1e1e2e;
  border: 1px solid #45475a;
}

.tag-card {
  cursor: default;
}

.tag-card:has(.n-checkbox) {
  cursor: pointer;
}
</style>
