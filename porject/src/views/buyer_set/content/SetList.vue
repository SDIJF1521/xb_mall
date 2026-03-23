<template>
<div class="set-list-wrapper">
  <!-- 主题切换 -->
  <div class="setting-item">
    <div class="setting-label">
      <el-icon class="setting-icon"><Moon v-if="darkMode" /><Sunny v-else /></el-icon>
      <span>主题模式</span>
    </div>
    <el-switch
      v-model="darkMode"
      active-text="黑夜模式"
      inactive-text="白天模式"
      style="--el-switch-on-color: #409eff; --el-switch-off-color: #f0a020"
      @change="toggleTheme"
    />
  </div>

  <el-divider />

  <!-- 操作按钮 -->
  <div class="setting-item">
    <el-button type="info" size="large" @click="exitLogin">退出登录</el-button>
    <el-button type="primary" size="large" @click="backToUser">回到用户端</el-button>
  </div>
</div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import router from '@/router'
import { ElMessage } from 'element-plus'
import { Moon, Sunny } from '@element-plus/icons-vue'
import BuyerTheme from '@/moon/buyer_theme'

defineOptions({ name: 'SetList' })

const Axios = axios.create({
  baseURL: 'http://127.0.0.1:8000/api'
})

const token = localStorage.getItem('buyer_access_token') || ''

// 主题状态
const darkMode = ref(false)
const buyerTheme = new BuyerTheme()

// 初始化主题
onMounted(() => {
  const saved = localStorage.getItem('buyer_theme')
  darkMode.value = saved === null ? true : saved === 'dark'
  buyerTheme.toggleTheme(darkMode.value)
})

// 切换主题
const toggleTheme = (value: boolean) => {
  document.documentElement.classList.add('theme-transition')
  buyerTheme.toggleTheme(value)
  localStorage.setItem('buyer_theme', value ? 'dark' : 'light')
  setTimeout(() => {
    document.documentElement.classList.remove('theme-transition')
  }, 300)
}

// 退出登录
const exitLogin = ref(async () => {
  const res = await Axios.post('/buter_exit', {}, { headers: { 'Access-Token': token } })
  if (res.status == 200) {
    if (res.data.current) {
      localStorage.removeItem('buyer_access_token')
      ElMessage.success(res.data.msg)
      router.push('/buyer_sing')
    } else {
      ElMessage.error(res.data.msg)
    }
  } else {
    ElMessage.error(res.data.msg)
  }
})

// 回到用户端
const backToUser = ref(() => {
  router.push('/')
})
</script>

<style scoped lang="scss">
.set-list-wrapper {
  width: 420px;
  padding: 24px;
  border-radius: 12px;
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-light);
  box-shadow: var(--el-box-shadow-light);
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  color: var(--el-text-color-primary);
}

.setting-icon {
  font-size: 18px;
  color: var(--el-color-primary);
}
</style>
