<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <h1>Info-Butler</h1>
        <p>智能信息管家</p>
      </div>

      <n-tabs v-model:value="activeTab" type="segment" animated>
        <n-tab-pane name="login" tab="登录">
          <n-form ref="loginFormRef" :model="loginForm" :rules="loginRules" @submit.prevent="handleLogin">
            <n-form-item label="用户名" path="username">
              <n-input v-model:value="loginForm.username" placeholder="输入用户名"
                :input-props="{ autocomplete: 'username' }">
                <template #prefix>
                  <n-icon>
                    <PersonOutline />
                  </n-icon>
                </template>
              </n-input>
            </n-form-item>
            <n-form-item label="密码" path="password">
              <n-input v-model:value="loginForm.password" type="password" show-password-on="click" placeholder="输入密码"
                :input-props="{ autocomplete: 'current-password' }" @keyup.enter="handleLogin">
                <template #prefix>
                  <n-icon>
                    <LockClosedOutline />
                  </n-icon>
                </template>
              </n-input>
            </n-form-item>
            <n-button type="primary" block strong :loading="loading" @click="handleLogin">登录</n-button>
          </n-form>
        </n-tab-pane>

        <n-tab-pane name="register" tab="注册">
          <n-form ref="registerFormRef" :model="registerForm" :rules="registerRules" @submit.prevent="handleRegister">
            <n-form-item label="用户名" path="username">
              <n-input v-model:value="registerForm.username" placeholder="3-50位，字母数字下划线">
                <template #prefix>
                  <n-icon>
                    <PersonOutline />
                  </n-icon>
                </template>
              </n-input>
            </n-form-item>
            <n-form-item label="邮箱" path="email">
              <n-input v-model:value="registerForm.email" placeholder="your@email.com">
                <template #prefix>
                  <n-icon>
                    <MailOutline />
                  </n-icon>
                </template>
              </n-input>
            </n-form-item>
            <n-form-item label="密码" path="password">
              <n-input v-model:value="registerForm.password" type="password" show-password-on="click"
                placeholder="至少6位">
                <template #prefix>
                  <n-icon>
                    <LockClosedOutline />
                  </n-icon>
                </template>
              </n-input>
            </n-form-item>
            <n-button type="primary" block strong :loading="loading" @click="handleRegister">注册</n-button>
          </n-form>
        </n-tab-pane>
      </n-tabs>

      <div v-if="errorMsg" class="error-msg">
        <n-alert type="error" :title="errorMsg" closable @close="errorMsg = ''" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { PersonOutline, LockClosedOutline, MailOutline } from '@vicons/ionicons5'
import api from '@/api'

const router = useRouter()
const message = useMessage()
const activeTab = ref('login')
const loading = ref(false)
const errorMsg = ref('')
const loginFormRef = ref<any>(null)
const registerFormRef = ref<any>(null)

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '' })

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '3-50位字母数字下划线', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { pattern: emailPattern, message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 128, message: '至少8位，需包含大小写字母和数字', trigger: 'blur' },
  ],
}

async function handleLogin() {
  if (!loginFormRef.value) return
  try {
    await loginFormRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  errorMsg.value = ''
  try {
    const res: any = await api.post('/auth/login', {
      username: loginForm.username,
      password: loginForm.password,
    })
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('user', JSON.stringify(res.user))
    api.defaults.headers.common['Authorization'] = `Bearer ${res.access_token}`
    message.success(`欢迎回来，${res.user.username}`)
    router.push('/digest/new')
  } catch (e: any) {
    const detail = e.response?.data?.detail
    if (Array.isArray(detail)) {
      errorMsg.value = detail.map((d: any) => d.msg || d).join('；')
    } else if (typeof detail === 'string') {
      errorMsg.value = detail
    } else {
      errorMsg.value = e.message || '登录失败'
    }
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!registerFormRef.value) return
  try {
    await registerFormRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  errorMsg.value = ''
  try {
    const res: any = await api.post('/auth/register', {
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password,
    })
    message.success('注册成功，请登录')
    activeTab.value = 'login'
    loginForm.username = registerForm.username
    loginForm.password = ''
  } catch (e: any) {
    const detail = e.response?.data?.detail
    if (Array.isArray(detail)) {
      errorMsg.value = detail.map((d: any) => d.msg || d).join('；')
    } else if (typeof detail === 'string') {
      errorMsg.value = detail
    } else {
      errorMsg.value = e.message || '注册失败'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #1e1e2e;
}

.login-card {
  width: 400px;
  padding: 32px;
  background: #181825;
  border-radius: 12px;
  border: 1px solid #313244;
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}

.login-header h1 {
  font-size: 28px;
  color: #89b4fa;
  letter-spacing: 2px;
  margin-bottom: 4px;
}

.login-header p {
  color: #6c7086;
  font-size: 14px;
}

.error-msg {
  margin-top: 16px;
}
</style>
