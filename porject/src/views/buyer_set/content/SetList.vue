<template>
<div class="set-list-outer">
  <!-- 页头 -->
  <div class="hero">
    <div class="hero-left">
      <div class="hero-icon-wrap">
        <el-icon :size="22"><Setting /></el-icon>
      </div>
      <div>
        <h2>基本设置</h2>
        <p>管理系统外观、账号与通用偏好。</p>
      </div>
    </div>
  </div>

  <!-- 账号信息 -->
  <el-card class="section-card" shadow="never">
    <template #header>
      <div class="card-head">
        <div class="card-head__left">
          <el-icon :size="16" color="var(--el-color-primary)"><User /></el-icon>
          <span class="card-head__title">账号信息</span>
        </div>
        <el-tag size="small" type="success" round effect="light">在线</el-tag>
      </div>
    </template>

    <div class="info-grid">
      <div class="info-item">
        <span class="info-label">登录身份</span>
        <el-tag size="small" :type="station === 'admin' ? 'danger' : 'primary'" round effect="plain">
          {{ station === 'admin' ? '主商户' : '店铺员工' }}
        </el-tag>
      </div>
      <div class="info-item">
        <span class="info-label">账号名</span>
        <span class="info-value">{{ userName || '--' }}</span>
      </div>
      <div class="info-item" v-if="mallCount">
        <span class="info-label">关联店铺</span>
        <span class="info-value">{{ mallCount }} 家</span>
      </div>
      <div class="info-item">
        <span class="info-label">Token 状态</span>
        <div class="token-indicator">
          <span class="token-dot" />
          <span class="info-value">有效</span>
        </div>
      </div>
    </div>
  </el-card>

  <!-- 外观设置 -->
  <el-card class="section-card" shadow="never">
    <template #header>
      <div class="card-head">
        <div class="card-head__left">
          <el-icon :size="16" color="var(--el-color-warning)"><Sunny /></el-icon>
          <span class="card-head__title">外观设置</span>
        </div>
      </div>
    </template>

    <div class="setting-row">
      <div class="setting-left">
        <div class="theme-preview" :class="darkMode ? 'is-dark' : 'is-light'">
          <div class="theme-preview__sidebar" />
          <div class="theme-preview__content">
            <div class="theme-preview__bar" />
            <div class="theme-preview__lines">
              <span /><span /><span />
            </div>
          </div>
        </div>
        <div class="setting-text">
          <span class="setting-title">主题模式</span>
          <span class="setting-desc">{{ darkMode ? '深色模式 — 减少视觉疲劳' : '浅色模式 — 清晰明亮' }}</span>
        </div>
      </div>
      <el-switch
        v-model="darkMode"
        :active-action-icon="Moon"
        :inactive-action-icon="Sunny"
        style="--el-switch-on-color: #2c3e50; --el-switch-off-color: #f39c12"
        @change="toggleTheme"
      />
    </div>
  </el-card>

  <!-- 操作 -->
  <el-card class="section-card" shadow="never">
    <template #header>
      <div class="card-head">
        <div class="card-head__left">
          <el-icon :size="16" color="var(--el-color-danger)"><Warning /></el-icon>
          <span class="card-head__title">账号操作</span>
        </div>
      </div>
    </template>

    <div class="action-list">
      <div class="action-row" @click="backToUser">
        <div class="action-row__left">
          <div class="action-icon-wrap is-primary">
            <el-icon :size="16"><HomeFilled /></el-icon>
          </div>
          <div class="action-text">
            <span class="action-title">回到用户端</span>
            <span class="action-desc">切换到消费者端浏览商城</span>
          </div>
        </div>
        <el-icon class="action-arrow"><ArrowRight /></el-icon>
      </div>

      <div class="action-divider" />

      <div class="action-row is-danger" @click="exitLogin">
        <div class="action-row__left">
          <div class="action-icon-wrap is-danger">
            <el-icon :size="16"><SwitchButton /></el-icon>
          </div>
          <div class="action-text">
            <span class="action-title">退出登录</span>
            <span class="action-desc">退出当前卖家端账号</span>
          </div>
        </div>
        <el-icon class="action-arrow"><ArrowRight /></el-icon>
      </div>
    </div>
  </el-card>

  <!-- 系统版本 -->
  <div class="sys-footer">
    <span>xb商城 卖家端 v1.0.0</span>
  </div>
</div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import router from '@/router'
import { ElMessage } from 'element-plus'
import {
  Moon, Sunny, Setting, SwitchButton, HomeFilled,
  User, Warning, ArrowRight,
} from '@element-plus/icons-vue'
import BuyerTheme from '@/moon/buyer_theme'

defineOptions({ name: 'SetList' })

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const token = localStorage.getItem('buyer_access_token') || ''

const darkMode = ref(false)
const buyerTheme = new BuyerTheme()

const userName = ref('')
const station = ref('')
const mallCount = ref(0)

function parseTokenInfo() {
  if (!token) return
  try {
    const b64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(b64))
    userName.value = payload.user || ''
    station.value = payload.station === '1' ? 'admin' : 'user'
    mallCount.value = payload.state_id_list?.length || (payload.mall_id ? 1 : 0)
  } catch { /* ignore */ }
}

onMounted(() => {
  const saved = localStorage.getItem('buyer_theme')
  darkMode.value = saved === null ? true : saved === 'dark'
  buyerTheme.toggleTheme(darkMode.value)
  parseTokenInfo()
})

const toggleTheme = (value: boolean) => {
  document.documentElement.classList.add('theme-transition')
  buyerTheme.toggleTheme(value)
  localStorage.setItem('buyer_theme', value ? 'dark' : 'light')
  setTimeout(() => document.documentElement.classList.remove('theme-transition'), 300)
}

const exitLogin = async () => {
  try {
    const res = await Axios.post('/buter_exit', {}, { headers: { 'Access-Token': token } })
    if (res.status === 200 && res.data.current) {
      localStorage.removeItem('buyer_access_token')
      ElMessage.success(res.data.msg)
      router.push('/buyer_sing')
    } else {
      ElMessage.error(res.data.msg || '退出失败')
    }
  } catch {
    ElMessage.error('请求失败')
  }
}

const backToUser = () => {
  router.push('/')
}
</script>

<style scoped lang="scss">
.set-list-outer {
  min-height: 400px;
  max-width: 620px;
}

/* ── 页头 ── */
.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.hero-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.hero-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--el-color-primary-light-8), var(--el-color-primary-light-5));
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.hero h2 {
  margin: 0 0 2px;
  font-size: 17px;
  font-weight: 700;
}

.hero p {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}

/* ── 通用卡片 ── */
.section-card {
  margin-bottom: 18px;
  border-radius: 14px;
  border: 1px solid var(--el-border-color-lighter);
  transition: box-shadow 0.3s;

  &:hover {
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05);
  }

  :deep(.el-card__header) {
    padding: 14px 20px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }

  :deep(.el-card__body) {
    padding: 20px;
  }
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-head__left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-head__title {
  font-weight: 700;
  font-size: 15px;
}

/* ── 账号信息网格 ── */
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  overflow: hidden;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  border-right: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
  transition: background 0.2s;

  &:hover {
    background: var(--el-fill-color-light);
  }

  &:nth-child(even) {
    border-right: none;
  }

  &:nth-last-child(-n+2) {
    border-bottom: none;
  }
}

.info-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.token-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
}

.token-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--el-color-success);
  box-shadow: 0 0 6px var(--el-color-success);
  animation: dot-pulse 2s infinite;
}

@keyframes dot-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ── 主题设置 ── */
.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
}

.setting-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 主题迷你预览图 */
.theme-preview {
  width: 52px;
  height: 36px;
  border-radius: 6px;
  display: flex;
  overflow: hidden;
  border: 2px solid var(--el-border-color-light);
  flex-shrink: 0;
  transition: all 0.4s;

  &.is-light {
    border-color: #f39c12;

    .theme-preview__sidebar {
      background: #ecf0f1;
    }

    .theme-preview__content {
      background: #ffffff;
    }

    .theme-preview__bar {
      background: #3498db;
    }

    .theme-preview__lines span {
      background: #e0e0e0;
    }
  }

  &.is-dark {
    border-color: #34495e;

    .theme-preview__sidebar {
      background: #1a1a2e;
    }

    .theme-preview__content {
      background: #2c3e50;
    }

    .theme-preview__bar {
      background: #409eff;
    }

    .theme-preview__lines span {
      background: #3d5066;
    }
  }
}

.theme-preview__sidebar {
  width: 12px;
  transition: background 0.4s;
}

.theme-preview__content {
  flex: 1;
  padding: 4px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  transition: background 0.4s;
}

.theme-preview__bar {
  height: 4px;
  border-radius: 1px;
  width: 70%;
  transition: background 0.4s;
}

.theme-preview__lines {
  display: flex;
  flex-direction: column;
  gap: 2px;

  span {
    height: 2px;
    border-radius: 1px;
    transition: background 0.4s;

    &:nth-child(1) { width: 100%; }
    &:nth-child(2) { width: 80%; }
    &:nth-child(3) { width: 60%; }
  }
}

.setting-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.setting-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.setting-desc {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

/* ── 操作列表 ── */
.action-list {
  padding: 0;
}

.action-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 8px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: var(--el-fill-color-light);
    padding-left: 12px;
  }

  &:active {
    transform: scale(0.99);
  }

  &.is-danger:hover {
    background: var(--el-color-danger-light-9);
  }
}

.action-row__left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.action-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  flex-shrink: 0;

  &.is-primary {
    background: var(--el-color-primary-light-9);
    color: var(--el-color-primary);
  }

  &.is-danger {
    background: var(--el-color-danger-light-9);
    color: var(--el-color-danger);
  }
}

.action-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.action-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.action-desc {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.action-arrow {
  font-size: 14px;
  color: var(--el-text-color-placeholder);
  transition: transform 0.2s;

  .action-row:hover & {
    transform: translateX(3px);
    color: var(--el-text-color-secondary);
  }
}

.action-divider {
  height: 1px;
  background: var(--el-border-color-lighter);
  margin: 4px 8px;
}

/* ── 底部版本号 ── */
.sys-footer {
  text-align: center;
  padding: 16px 0 4px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  letter-spacing: 0.3px;
}
</style>
