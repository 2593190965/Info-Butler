<template>
  <div class="settings-page">
    <n-card title="个人设置" :bordered="false" class="settings-card">
      <n-descriptions label-placement="left" :column="1" bordered>
        <n-descriptions-item label="用户名">
          {{ currentUser?.username || '-' }}
        </n-descriptions-item>
        <n-descriptions-item label="邮箱">
          {{ currentUser?.email || '-' }}
        </n-descriptions-item>
      </n-descriptions>
    </n-card>

    <n-card title="飞书账号绑定" :bordered="false" class="settings-card" style="margin-top: 16px">
      <template v-if="bindingStatus?.has_linked">
        <n-space vertical>
          <n-alert type="success" title="已绑定飞书账号">
            您的飞书账号已成功关联，可以在飞书中使用机器人管理待办事项。
          </n-alert>
          <n-button type="error" ghost :loading="unbinding" @click="handleUnbind">
            解绑飞书账号
          </n-button>
        </n-space>
      </template>
      <template v-else>
        <n-space vertical>
          <n-alert type="info" title="未绑定飞书账号">
            绑定飞书账号后，可通过飞书机器人添加和查询待办事项，数据与网页端实时同步。
          </n-alert>
          <div v-if="bindingCode" class="binding-code-section">
            <n-alert type="warning" style="margin-bottom: 12px">
              绑定码 5 分钟内有效，请尽快完成绑定。
            </n-alert>
            <div class="binding-code-display">
              <code class="binding-code">{{ bindingCode }}</code>
              <n-button size="small" @click="copyBindingCode">复制</n-button>
            </div>
            <n-steps :current="bindingStep" vertical size="small" style="margin-top: 16px">
              <n-step title="获取绑定码" />
              <n-step title="在飞书中@机器人发送" description="绑定 + 绑定码" />
              <n-step title="绑定完成" />
            </n-steps>
          </div>
          <n-space>
            <n-button type="primary" :loading="generating" @click="handleGenerateCode">
              {{ bindingCode ? '重新生成绑定码' : '生成绑定码' }}
            </n-button>
            <n-button v-if="bindingCode" :loading="checking" @click="checkBindingStatus">
              检查绑定状态
            </n-button>
          </n-space>
        </n-space>
      </template>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import api from '@/api'

const message = useMessage()
const dialog = useDialog()

const currentUser = ref<any>(null)
const bindingStatus = ref<{ has_linked: boolean; feishu_open_id: string | null } | null>(null)
const bindingCode = ref('')
const bindingStep = ref(1)
const generating = ref(false)
const checking = ref(false)
const unbinding = ref(false)

onMounted(() => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    try { currentUser.value = JSON.parse(userStr) } catch { /* ignore */ }
  }
  checkBindingStatus()
})

async function checkBindingStatus() {
  checking.value = true
  try {
    const res: any = await api.get('/feishu/status')
    bindingStatus.value = res
    if (res?.has_linked && bindingCode.value) {
      bindingStep.value = 3
      message.success('飞书账号绑定成功！')
      bindingCode.value = ''
    }
  } catch (e: any) {
    message.error(e.message || '查询绑定状态失败')
  } finally {
    checking.value = false
  }
}

async function handleGenerateCode() {
  generating.value = true
  try {
    const res: any = await api.post('/feishu/generate-binding-code')
    bindingCode.value = res.binding_code
    bindingStep.value = 1
    message.success('绑定码已生成')
  } catch (e: any) {
    const detail = e.response?.data?.detail || e.message
    message.error(detail || '生成绑定码失败')
  } finally {
    generating.value = false
  }
}

function copyBindingCode() {
  const text = `绑定 ${bindingCode.value}`
  navigator.clipboard.writeText(text).then(() => {
    message.success('已复制到剪贴板')
    bindingStep.value = 2
  }).catch(() => {
    message.error('复制失败，请手动复制')
  })
}

function handleUnbind() {
  dialog.warning({
    title: '确认解绑',
    content: '解绑后将无法在飞书中使用机器人管理待办事项，确定要解绑吗？',
    positiveText: '确认解绑',
    negativeText: '取消',
    onPositiveClick: async () => {
      unbinding.value = true
      try {
        await api.post('/feishu/unbind')
        bindingStatus.value = { has_linked: false, feishu_open_id: null }
        message.success('已解绑飞书账号')
      } catch (e: any) {
        const detail = e.response?.data?.detail || e.message
        message.error(detail || '解绑失败')
      } finally {
        unbinding.value = false
      }
    },
  })
}
</script>

<style scoped>
.settings-page {
  max-width: 640px;
}

.settings-card {
  background: #181825;
  border: 1px solid #313244;
}

.binding-code-section {
  background: #1e1e2e;
  border: 1px solid #313244;
  border-radius: 8px;
  padding: 16px;
}

.binding-code-display {
  display: flex;
  align-items: center;
  gap: 12px;
}

.binding-code {
  font-size: 20px;
  font-weight: bold;
  color: #89b4fa;
  letter-spacing: 2px;
  background: #11111b;
  padding: 8px 16px;
  border-radius: 6px;
  flex: 1;
  text-align: center;
}
</style>
