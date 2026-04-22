<template>
  <n-config-provider :theme="theme">
    <n-message-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <n-loading-bar-provider>
            <div class="app-container">
              <aside class="sidebar">
                <div class="logo">
                  <h1>Info-Butler</h1>
                </div>
                <n-menu :options="menuOptions" :value="currentRoute" @update:value="handleMenuUpdate" />
                <div v-if="currentUser" class="user-section">
                  <n-divider style="margin: 8px 0" />
                  <div class="user-info">
                    <span class="username">{{ currentUser.username }}</span>
                    <n-button text size="small" type="error" @click="handleLogout">退出</n-button>
                  </div>
                </div>
              </aside>
              <main class="main-content">
                <router-view />
              </main>
            </div>
          </n-loading-bar-provider>
        </n-notification-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { h, computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  darkTheme,
  NConfigProvider,
  NMessageProvider,
  NDialogProvider,
  NNotificationProvider,
  NLoadingBarProvider,
  NMenu,
  NIcon,
  NDivider,
  NButton,
  type MenuOption,
} from 'naive-ui'
import {
  CreateOutline,
  ListOutline,
  CheckboxOutline,
  StatsChartOutline,
  PricetagsOutline,
} from '@vicons/ionicons5'
import api from '@/api'

const route = useRoute()
const router = useRouter()

const theme = darkTheme
const currentUser = ref<any>(null)

onMounted(() => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    try {
      currentUser.value = JSON.parse(userStr)
    } catch {
      currentUser.value = null
    }
  }
})

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  delete api.defaults.headers.common['Authorization']
  currentUser.value = null
  router.push('/login')
}

const currentRoute = computed(() => route.path)

function renderIcon(icon: any) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions: MenuOption[] = [
  {
    label: '信息录入',
    key: '/digest/new',
    icon: renderIcon(CreateOutline),
  },
  {
    label: '知识卡片',
    key: '/digest/list',
    icon: renderIcon(ListOutline),
  },
  {
    label: '行动项',
    key: '/actions',
    icon: renderIcon(CheckboxOutline),
  },
  {
    label: '标签管理',
    key: '/tags',
    icon: renderIcon(PricetagsOutline),
  },
  {
    label: '周报复盘',
    key: '/review',
    icon: renderIcon(StatsChartOutline),
  },
]

function handleMenuUpdate(key: string) {
  router.push(key)
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.app-container {
  display: flex;
  min-height: 100vh;
  background: #1e1e2e;
  color: #cdd6f4;
}

.sidebar {
  width: 220px;
  background: #181825;
  border-right: 1px solid #313244;
  padding: 20px 0;
  position: fixed;
  height: 100vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.logo {
  text-align: center;
  padding: 0 20px 20px;
  border-bottom: 1px solid #313244;
  margin-bottom: 10px;
}

.logo h1 {
  font-size: 18px;
  color: #89b4fa;
  letter-spacing: 1px;
}

.user-section {
  margin-top: auto;
  padding: 0 16px 16px;
}

.user-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.username {
  font-size: 13px;
  color: #a6adc8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 120px;
}

.main-content {
  margin-left: 220px;
  flex: 1;
  padding: 24px;
  max-width: 1200px;
}
</style>
