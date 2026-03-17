<template>
  <el-container class="cs-container">
    <!-- 顶部导航 -->
    <el-header class="cs-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" text class="back-btn" @click="router.back()">返回</el-button>
        <div class="header-title">
          <el-icon class="title-icon"><Headset /></el-icon>
          <span>在线客服管理</span>
          <el-tag
            :type="wsState === 'open' ? 'success' : wsState === 'connecting' ? 'warning' : 'danger'"
            size="small"
          >
            {{ wsStateLabel }}
          </el-tag>
        </div>
      </div>
      <div class="header-right">
        <el-tooltip content="重新连接" placement="bottom">
          <el-button
            :icon="Refresh"
            circle
            size="small"
            :loading="wsState === 'connecting'"
            @click="reconnect"
          />
        </el-tooltip>
      </div>
    </el-header>

    <!-- 主体 -->
    <el-container class="cs-body">
      <!-- 左侧会话列表 -->
      <el-aside width="280px" class="cs-aside">
        <div class="aside-title">
          <el-icon><User /></el-icon>
          用户会话
          <el-badge :value="onlineSessions" type="success" class="online-badge" />
        </div>
        <SessionList
          :sessions="sessions"
          :active-session-id="activeSessionId"
          :loading="sessionsLoading"
          @select="onSelectSession"
        />
      </el-aside>

      <!-- 右侧聊天窗口 -->
      <el-main class="cs-main">
        <ChatWindow
          :session-id="activeSessionId"
          :is-online="isActiveOnline"
          :messages="activeMessages"
          :history-loading="historyLoading"
          :ws-state="wsState"
          @send="onSendMessage"
        />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, Refresh, User, Headset,
} from '@element-plus/icons-vue'

import BuyerTheme from '@/moon/buyer_theme'
import SessionList from './components/SessionList.vue'
import ChatWindow from './components/ChatWindow.vue'
import type { Session } from './components/SessionList.vue'
import type { CsMsg } from './components/ChatWindow.vue'

// ── 路由 ──────────────────────────────────────────────────────────────────────
const route = useRoute()
const router = useRouter()
const mallId = Number(route.params.mall_id)

// ── 状态 ──────────────────────────────────────────────────────────────────────
const sessions = ref<Session[]>([])
const sessionsLoading = ref(false)
const activeSessionId = ref('')
// { session_id -> CsMsg[] }
const sessionMessages = ref<Record<string, CsMsg[]>>({})
const historyLoading = ref(false)

type WsState = 'connecting' | 'open' | 'closed'
const wsState = ref<WsState>('connecting')

const wsStateLabel = computed(() => {
  if (wsState.value === 'open') return '已连接'
  if (wsState.value === 'connecting') return '连接中'
  return '已断开'
})

const activeMessages = computed<CsMsg[]>(
  () => sessionMessages.value[activeSessionId.value] || []
)

const isActiveOnline = computed(() =>
  sessions.value.find(s => s.session_id === activeSessionId.value)?.online ?? false
)

const onlineSessions = computed(() => sessions.value.filter(s => s.online).length)

// ── WebSocket ─────────────────────────────────────────────────────────────────
let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let autoReconnect = true

function getToken(): string {
  return localStorage.getItem('buyer_access_token') || ''
}

function connect() {
  const token = getToken()
  if (!token) {
    ElMessage.error('未检测到登录信息，请重新登录')
    return
  }

  wsState.value = 'connecting'
  const encodedToken = encodeURIComponent(token)
  ws = new WebSocket(
    `ws://127.0.0.1:8000/api/ws/customer_service/${mallId}?token=${encodedToken}&client_type=seller`
  )

  ws.onopen = () => {
    wsState.value = 'open'
  }

  ws.onmessage = (event) => {
    try {
      handleServerMessage(JSON.parse(event.data))
    } catch {
      // ignore
    }
  }

  ws.onerror = () => {
    wsState.value = 'closed'
    ElMessage.error('WebSocket 连接出错')
  }

  ws.onclose = (e) => {
    wsState.value = 'closed'
    if (e.code === 4001 || e.code === 4002) {
      ElMessage.error('认证失败，请重新登录')
      autoReconnect = false
    } else if (autoReconnect) {
      reconnectTimer = setTimeout(connect, 3000)
    }
  }
}

function handleServerMessage(data: any) {
  if (data.type === 'session_list') {
    sessionsLoading.value = false
    sessions.value = (data.data || []).map((s: any) => ({
      session_id: s.session_id,
      online: s.online,
      last_message: s.last_message || '',
      last_time: formatTime(s.last_time),
    }))
    return
  }

  if (data.type === 'system') {
    return
  }

  if (data.type === 'history') {
    historyLoading.value = false
    const sid: string = data.session_id || activeSessionId.value
    sessionMessages.value[sid] = (data.data || []).map(normalizeMsg)
    return
  }

  if (data.type === 'chat') {
    const sid: string = data.session_id || activeSessionId.value
    if (!sessionMessages.value[sid]) {
      sessionMessages.value[sid] = []
    }
    sessionMessages.value[sid].push(normalizeMsg(data))

    // 更新会话列表中的最后一条消息
    const idx = sessions.value.findIndex(s => s.session_id === sid)
    if (idx !== -1) {
      sessions.value[idx] = {
        ...sessions.value[idx],
        last_message: data.message_type === 'product_card' ? `[商品] ${data.content}` : data.content,
        last_time: formatTime(data.created_at),
      }
    } else if (data.sender_type === 'user') {
      // 新会话
      sessions.value.unshift({
        session_id: sid,
        online: true,
        last_message: data.content,
        last_time: formatTime(data.created_at),
      })
    }
    return
  }
}

function normalizeMsg(m: any): CsMsg {
  return {
    sender_type: m.sender_type || 'user',
    sender_name: m.sender_name,
    content: m.content || '',
    message_type: m.message_type || 'text',
    product_info: m.product_info,
    created_at: formatTime(m.created_at),
  }
}

function onSendMessage(content: string) {
  if (!activeSessionId.value || wsState.value !== 'open') return
  if (content.length > 500) {
    ElMessage.warning('消息不能超过 500 字')
    return
  }
  ws?.send(JSON.stringify({
    type: 'chat',
    content,
    target_session: activeSessionId.value,
  }))
}

function onSelectSession(sessionId: string) {
  activeSessionId.value = sessionId
  // 如果本地没有历史，拉取一次
  if (!sessionMessages.value[sessionId]) {
    historyLoading.value = true
    ws?.send(JSON.stringify({ type: 'fetch_history', session_id: sessionId }))
  }
}

function disconnect() {
  autoReconnect = false
  if (reconnectTimer) clearTimeout(reconnectTimer)
  ws?.close()
  ws = null
}

function reconnect() {
  disconnect()
  autoReconnect = true
  connect()
}

// ── 辅助 ─────────────────────────────────────────────────────────────────────
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

// ── 生命周期 ──────────────────────────────────────────────────────────────────
onMounted(() => {
  new BuyerTheme().toggleTheme(true)
  sessionsLoading.value = true
  connect()
})

onBeforeUnmount(() => {
  disconnect()
})
</script>

<style scoped lang="scss">
.cs-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

/* ── Header ── */
.cs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.title-icon {
  font-size: 20px;
  color: #667eea;
}

/* ── Body ── */
.cs-body {
  flex: 1;
  overflow: hidden;
}

/* ── Aside ── */
.cs-aside {
  border-right: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.aside-title {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 14px 16px 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  border-bottom: 1px solid var(--el-border-color-light);
  flex-shrink: 0;
}

.online-badge {
  margin-left: auto;
}

/* ── Main ── */
.cs-main {
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
