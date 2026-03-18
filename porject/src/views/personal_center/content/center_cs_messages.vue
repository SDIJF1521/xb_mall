<template>
  <div class="cs-messages-container">
    <!-- 头部区域：与 CustomerService 风格一致 -->
    <div class="cs-header">
      <div class="cs-header-inner">
        <div class="cs-header-icon">
          <el-icon :size="28"><Service /></el-icon>
        </div>
        <div class="cs-header-text">
          <span class="cs-title">客服消息</span>
          <span class="cs-subtitle">查看与各店铺客服的交流记录</span>
        </div>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="cs-loading">
      <el-skeleton :rows="4" animated />
    </div>

    <!-- 空状态 -->
    <el-empty v-else-if="sessions.length === 0" description="暂无客服消息记录" class="cs-empty">
      <template #image>
        <div class="empty-icon-wrap">
          <el-icon :size="64"><ChatDotRound /></el-icon>
        </div>
      </template>
    </el-empty>

    <!-- 会话列表 -->
    <div v-else class="session-list">
      <div
        v-for="item in sessions"
        :key="item.mall_id"
        class="session-item"
        :class="{ expanded: expandedMallId === item.mall_id }"
      >
        <div class="session-summary" @click="toggleSession(item.mall_id)">
          <div class="session-left">
            <div class="session-avatar">
              <el-icon :size="20"><Service /></el-icon>
            </div>
            <div class="session-info">
              <span class="session-name">{{ item.mall_name }}</span>
              <span class="session-preview">{{ item.last_message || '暂无消息' }}</span>
              <span class="session-time">{{ formatTime(item.last_time) }}</span>
            </div>
          </div>
          <div class="session-right">
            <el-badge
              v-if="item.unread_count > 0"
              :value="item.unread_count"
              :max="99"
              class="session-badge"
            />
            <el-icon class="expand-icon">
              <ArrowDown v-if="expandedMallId !== item.mall_id" />
              <ArrowUp v-else />
            </el-icon>
          </div>
        </div>

        <!-- 展开的消息历史 -->
        <transition name="detail-slide">
          <div v-show="expandedMallId === item.mall_id" class="session-detail">
            <div v-if="historyLoading[item.mall_id]" class="history-loading">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>加载中...</span>
            </div>
            <div v-else class="message-list" ref="msgListRef">
              <div
                v-for="(msg, idx) in (historyMap[item.mall_id] || [])"
                :key="idx"
                class="message-row"
                :class="msg.sender_type === 'user' ? 'message-row--user' : 'message-row--seller'"
              >
                <div class="message-avatar">
                  <el-icon v-if="msg.sender_type === 'seller'"><Service /></el-icon>
                  <span v-else>我</span>
                </div>
                <div class="message-content">
                  <div v-if="msg.sender_type === 'seller'" class="message-sender">客服</div>
                  <!-- 商品卡片：与 CustomerService 风格一致 -->
                  <div
                    v-if="msg.message_type === 'product_card' && msg.product_info"
                    class="product-card-msg"
                    :class="msg.sender_type === 'user' ? 'product-card--user' : 'product-card--seller'"
                  >
                    <div v-if="msg.product_info.img" class="pc-img-wrap">
                      <img :src="getProductImg(msg.product_info)" class="pc-img" alt="商品" />
                    </div>
                    <div class="pc-body">
                      <div class="pc-name">{{ msg.product_info.name }}</div>
                      <div v-if="msg.product_info.spec" class="pc-spec">{{ msg.product_info.spec }}</div>
                      <div v-if="msg.product_info.price" class="pc-price">¥{{ msg.product_info.price }}</div>
                      <a
                        v-if="msg.product_info.url"
                        :href="msg.product_info.url"
                        target="_blank"
                        class="pc-link"
                      >
                        查看商品详情 →
                      </a>
                    </div>
                  </div>
                  <!-- 普通文本消息 -->
                  <div v-else class="message-text">{{ msg.content }}</div>
                  <div class="message-time">{{ formatMsgTime(msg.created_at) }}</div>
                </div>
              </div>
            </div>
            <div class="session-actions">
              <el-button
                type="primary"
                size="small"
                round
                class="go-store-btn"
                @click="goToStore(item.mall_id)"
              >
                <el-icon><Shop /></el-icon>
                前往店铺继续咨询
              </el-button>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Service, ArrowDown, ArrowUp, Loading, Shop, ChatDotRound } from '@element-plus/icons-vue'

const emit = defineEmits<{ (e: 'read'): void }>()
defineOptions({ name: 'CenterCsMessages' })

const router = useRouter()
const token = localStorage.getItem('access_token') || ''

const Axios = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  headers: { 'access-token': token },
})

interface SessionItem {
  mall_id: number
  mall_name: string
  last_message: string
  last_time: string
  unread_count: number
}

interface CsMessage {
  sender_type: string
  sender_name?: string
  content: string
  message_type?: string
  product_info?: { name: string; spec?: string; url?: string; img?: string; price?: string }
  created_at: string
}

/** 商品图片：支持 base64 或 data URL */
function getProductImg(info: { img?: string }): string {
  const raw = info?.img || ''
  if (!raw) return ''
  return raw.startsWith('data:') ? raw : `data:image/jpeg;base64,${raw}`
}

const loading = ref(false)
const sessions = ref<SessionItem[]>([])
const expandedMallId = ref<number | null>(null)
const historyMap = ref<Record<number, CsMessage[]>>({})
const historyLoading = ref<Record<number, boolean>>({})
const msgListRef = ref<HTMLElement | null>(null)

async function fetchSessions() {
  loading.value = true
  try {
    const res = await Axios.get('/cs_user_sessions')
    if (res.data.current && res.data.data) {
      sessions.value = res.data.data
    } else {
      ElMessage.error(res.data.msg || '获取会话列表失败')
    }
  } catch {
    ElMessage.error('网络异常，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function fetchHistory(mallId: number) {
  historyLoading.value = { ...historyLoading.value, [mallId]: true }
  try {
    const res = await Axios.get('/cs_user_history', {
      params: { mall_id: mallId, page: 1, page_size: 80 },
    })
    if (res.data.current && res.data.data) {
      historyMap.value = { ...historyMap.value, [mallId]: res.data.data }
      emit('read') // 已读后通知父组件刷新未读数
    }
  } catch {
    ElMessage.error('加载消息失败')
  } finally {
    historyLoading.value = { ...historyLoading.value, [mallId]: false }
  }
}

function toggleSession(mallId: number) {
  if (expandedMallId.value === mallId) {
    expandedMallId.value = null
    return
  }
  expandedMallId.value = mallId
  if (!historyMap.value[mallId]) {
    fetchHistory(mallId)
  }
}

function goToStore(mallId: number) {
  router.push(`/store/${mallId}`)
}

function formatTime(ts: string): string {
  if (!ts) return ''
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ts
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  const sameDay =
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  if (sameDay) {
    return `${pad(d.getHours())}:${pad(d.getMinutes())}`
  }
  return `${pad(d.getMonth() + 1)}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function formatMsgTime(ts: string): string {
  if (!ts) return ''
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ts
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(() => {
  if (!token) {
    ElMessage.warning('请先登录')
    return
  }
  fetchSessions()
})
</script>

<style scoped>
.cs-messages-container {
  padding: 20px;
  max-width: 560px;
  margin: 0 auto;
}

.cs-header {
  margin-bottom: 20px;
}

.cs-title {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.cs-subtitle {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.cs-loading {
  padding: 20px 0;
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.session-item {
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  overflow: hidden;
  background: var(--el-bg-color);
}

.session-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.session-summary:hover {
  background: var(--el-fill-color-light);
}

.session-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.session-icon {
  font-size: 24px;
  color: #667eea;
  flex-shrink: 0;
}

.session-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.session-name {
  font-weight: 600;
  font-size: 15px;
  color: var(--el-text-color-primary);
}

.session-preview {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-time {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.session-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.session-badge :deep(.el-badge__content) {
  background: #f56c6c;
}

.expand-icon {
  font-size: 16px;
  color: var(--el-text-color-placeholder);
}

.session-detail {
  border-top: 1px solid var(--el-border-color-lighter);
  padding: 12px 16px;
  background: var(--el-fill-color-extra-light);
}

.history-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: var(--el-text-color-placeholder);
}

.message-list {
  max-height: 280px;
  overflow-y: auto;
  padding: 8px 0;
}

.message-list::-webkit-scrollbar {
  width: 4px;
}

.message-row {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.message-row--user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  flex-shrink: 0;
}

.message-row--user .message-avatar {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.message-content {
  max-width: 75%;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.message-row--user .message-content {
  align-items: flex-end;
}

.message-sender {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.message-text {
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
}

.message-row--user .message-text {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border: none;
}

.product-card-msg {
  padding: 8px 12px;
  border-radius: 12px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
}

.pc-name {
  font-weight: 600;
  font-size: 13px;
}

.pc-spec {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.pc-link {
  font-size: 12px;
  color: #409eff;
  margin-top: 6px;
  display: inline-block;
}

.message-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.session-actions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
