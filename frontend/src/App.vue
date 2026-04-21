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
import { h, computed } from 'vue'
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
  type MenuOption,
} from 'naive-ui'
import {
  CreateOutline,
  ListOutline,
  CheckboxOutline,
  StatsChartOutline,
} from '@vicons/ionicons5'

const route = useRoute()
const router = useRouter()

const theme = darkTheme

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

.main-content {
  margin-left: 220px;
  flex: 1;
  padding: 24px;
  max-width: 1200px;
}
</style>
