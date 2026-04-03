<template>
  <div class="sys-params">
    <div class="hero">
      <div class="hero-text">
        <h2>系统参数</h2>
        <p>查看运行环境、进行系统连通性测试和账号管理。</p>
      </div>
    </div>

    <!-- 系统信息 -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="card-head">
          <span class="card-head__title">运行环境</span>
        </div>
      </template>
      <div v-if="sysInfo" class="sys-info-grid">
        <div class="sys-info-item">
          <span class="sys-info-label">Python</span>
          <span class="sys-info-val">{{ sysInfo.python_version }}</span>
        </div>
        <div class="sys-info-item">
          <span class="sys-info-label">操作系统</span>
          <span class="sys-info-val">{{ sysInfo.os }}</span>
        </div>
        <div class="sys-info-item">
          <span class="sys-info-label">架构</span>
          <span class="sys-info-val">{{ sysInfo.arch }}</span>
        </div>
      </div>
      <div v-else class="sys-info-empty">运行系统测试后显示</div>
    </el-card>

    <!-- 系统测试 -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="card-head">
          <span class="card-head__title">系统测试</span>
          <el-button type="primary" plain :loading="testing" @click="runHealthCheck">
            {{ testing ? '检测中...' : '开始检测' }}
          </el-button>
        </div>
      </template>

      <div v-if="!checks.length && !testing" class="test-placeholder">
        <p>点击"开始检测"按钮，系统将自动检测以下服务的连通性：</p>
        <div class="test-placeholder-list">
          <span>MySQL 数据库</span>
          <span>Redis 缓存</span>
          <span>MongoDB 文档库</span>
          <span>SMTP 邮件服务</span>
        </div>
      </div>

      <div v-if="checks.length" class="check-list">
        <div v-for="(item, idx) in checks" :key="idx" class="check-item" :class="{ 'is-ok': item.ok, 'is-fail': !item.ok }">
          <div class="check-icon">
            <span v-if="item.ok">&#10003;</span>
            <span v-else>&#10007;</span>
          </div>
          <div class="check-body">
            <div class="check-name">{{ item.name }}</div>
            <div class="check-msg">{{ item.msg }}</div>
          </div>
        </div>
      </div>

      <div v-if="checks.length" class="check-summary">
        <el-tag :type="allOk ? 'success' : 'danger'" size="default">
          {{ allOk ? '全部服务正常' : `${failCount} 项异常` }}
        </el-tag>
        <span class="check-time" v-if="lastCheckTime">检测时间：{{ lastCheckTime }}</span>
      </div>
    </el-card>

    <!-- 账号操作 -->
    <el-card class="section-card section-card--danger" shadow="never">
      <template #header>
        <div class="card-head">
          <span class="card-head__title">账号操作</span>
        </div>
      </template>
      <div class="logout-section">
        <div class="logout-info">
          <div class="logout-title">退出登录</div>
          <div class="logout-desc">清除当前管理员会话，退出后需要重新登录。</div>
        </div>
        <el-button type="danger" plain @click="handleLogout">退出登录</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'

defineOptions({ name: 'SystemParameters' })

const router = useRouter()
const API = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const token = localStorage.getItem('admin_access_token') || ''
function hdr() {
  return { 'access-token': token }
}

interface CheckItem {
  name: string
  ok: boolean
  msg: string
}

const testing = ref(false)
const checks = ref<CheckItem[]>([])
const sysInfo = ref<{ python_version: string; os: string; arch: string } | null>(null)
const lastCheckTime = ref('')

const allOk = computed(() => checks.value.every(c => c.ok))
const failCount = computed(() => checks.value.filter(c => !c.ok).length)

async function runHealthCheck() {
  testing.value = true
  checks.value = []
  try {
    const { data } = await API.get('/manage_system_health', { headers: hdr() })
    if (data.success && data.data) {
      checks.value = data.data.checks || []
      sysInfo.value = data.data.sys_info || null
      const now = new Date()
      lastCheckTime.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
    } else {
      ElMessage.error(data.msg || '检测失败')
    }
  } catch {
    ElMessage.error('系统检测请求失败')
  } finally {
    testing.value = false
  }
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？退出后需要重新输入账号密码。', '退出确认', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
    localStorage.removeItem('admin_access_token')
    localStorage.removeItem('admin_refresh_token')
    sessionStorage.removeItem('admin_permissions')
    ElMessage.success('已退出登录')
    router.push('/management_login')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.sys-params {
  min-height: 400px;
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px 16px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.hero-text h2 {
  margin: 0 0 4px;
  font-size: 17px;
  font-weight: 600;
}

.hero-text p {
  margin: 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.45;
}

.section-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
}

.section-card :deep(.el-card__header) {
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.section-card :deep(.el-card__body) {
  padding: 20px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.card-head__title {
  font-weight: 600;
  font-size: 15px;
}

/* 系统信息 */
.sys-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.sys-info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 16px;
  background: var(--el-fill-color-extra-light);
  border-radius: 8px;
}

.sys-info-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.sys-info-val {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  font-family: ui-monospace, 'Cascadia Code', monospace;
}

.sys-info-empty {
  text-align: center;
  color: var(--el-text-color-placeholder);
  font-size: 13px;
  padding: 12px 0;
}

/* 测试占位 */
.test-placeholder {
  text-align: center;
  padding: 16px 0;
}

.test-placeholder p {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  margin: 0 0 12px;
}

.test-placeholder-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.test-placeholder-list span {
  background: var(--el-fill-color-extra-light);
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 12px;
  color: var(--el-text-color-regular);
}

/* 检测结果 */
.check-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.check-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
  transition: all 0.2s;
}

.check-item.is-ok {
  border-color: var(--el-color-success-light-5);
  background: var(--el-color-success-light-9);
}

.check-item.is-fail {
  border-color: var(--el-color-danger-light-5);
  background: var(--el-color-danger-light-9);
}

.check-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
  flex-shrink: 0;
}

.check-item.is-ok .check-icon {
  background: var(--el-color-success);
  color: #fff;
}

.check-item.is-fail .check-icon {
  background: var(--el-color-danger);
  color: #fff;
}

.check-body {
  flex: 1;
  min-width: 0;
}

.check-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.check-msg {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.check-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.check-time {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

/* 登出 */
.section-card--danger {
  border-color: var(--el-color-danger-light-7);
}

.logout-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.logout-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.logout-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
</style>
