<template>
  <el-container class="chat-container">
    <!-- 顶部导航栏 -->
    <el-header class="chat-header">
      <div class="header-left">
        <el-button
          :icon="ArrowLeft"
          text
          class="back-btn"
          @click="goBack"
        >返回</el-button>
        <div class="header-title">
          <el-icon class="title-icon"><ChatDotRound /></el-icon>
          <span>店铺内部聊天室</span>
          <el-tag
            :type="wsState === 'open' ? 'success' : wsState === 'connecting' ? 'warning' : 'danger'"
            size="small"
            class="status-tag"
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

    <el-container class="chat-body">
      <!-- 在线用户侧边栏 -->
      <el-aside width="200px" class="online-aside">
        <div class="aside-title">
          <el-icon><User /></el-icon>
          在线成员
          <el-badge :value="onlineUsers.length" class="online-count" />
        </div>
        <div class="online-list">
          <div
            v-for="user in onlineUsers"
            :key="user"
            class="online-item"
            :class="{ 'online-item--self': user === currentUser }"
          >
            <span class="online-dot" />
            <span class="online-name">{{ user }}{{ user === currentUser ? '（我）' : '' }}</span>
          </div>
          <div v-if="onlineUsers.length === 0" class="no-online">暂无在线成员</div>
        </div>
      </el-aside>

      <!-- 主聊天区域 -->
      <el-main class="chat-main">
        <!-- 消息列表 -->
        <div ref="msgListRef" class="msg-list">
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="msg-row"
            :class="{
              'msg-row--self': msg.type === 'chat' && msg.username === currentUser,
              'msg-row--system': msg.type === 'system',
            }"
          >
            <!-- 系统消息 -->
            <template v-if="msg.type === 'system'">
              <div class="sys-msg">
                <el-icon><InfoFilled /></el-icon>
                {{ msg.content }}
                <span class="msg-time">{{ formatTime(msg.created_at) }}</span>
              </div>
            </template>

            <!-- 聊天消息 -->
            <template v-else-if="msg.type === 'chat'">
              <!-- 他人消息 -->
              <template v-if="msg.username !== currentUser">
                <div class="avatar-wrap avatar-wrap--other">
                  <div class="avatar">{{ msg.username?.slice(0, 1).toUpperCase() }}</div>
                </div>
                <div class="bubble-wrap bubble-wrap--other">
                  <div class="msg-sender">{{ msg.username }}</div>
                  <div class="bubble bubble--other">{{ msg.content }}</div>
                  <div class="msg-time">{{ formatTime(msg.created_at) }}</div>
                </div>
              </template>

              <!-- 自己的消息 -->
              <template v-else>
                <div class="bubble-wrap bubble-wrap--self">
                  <div class="bubble bubble--self">{{ msg.content }}</div>
                  <div class="msg-time msg-time--self">{{ formatTime(msg.created_at) }}</div>
                </div>
                <div class="avatar-wrap avatar-wrap--self">
                  <div class="avatar avatar--self">{{ msg.username?.slice(0, 1).toUpperCase() }}</div>
                </div>
              </template>
            </template>
          </div>

          <!-- 加载提示 -->
          <div v-if="messages.length === 0 && wsState === 'open'" class="empty-hint">
            <el-icon :size="40"><ChatRound /></el-icon>
            <p>暂无消息，快来发第一条消息吧！</p>
          </div>

          <!-- 连接中 -->
          <div v-if="wsState !== 'open'" class="connecting-hint">
            <el-icon class="is-loading" :size="32"><Loading /></el-icon>
            <p>{{ wsState === 'connecting' ? '正在连接聊天室...' : '连接已断开，请点击右上角重新连接' }}</p>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="3"
            placeholder="输入消息，Enter 发送，Shift+Enter 换行"
            :disabled="wsState !== 'open'"
            resize="none"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <div class="input-actions">
            <span class="input-tip">{{ inputText.length }}/500</span>
            <el-button
              type="primary"
              :icon="Promotion"
              :disabled="wsState !== 'open' || !inputText.trim()"
              @click="sendMessage"
            >发送</el-button>
          </div>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Refresh,
  Promotion,
  User,
  ChatDotRound,
  ChatRound,
  InfoFilled,
  Loading,
} from '@element-plus/icons-vue'
import BuyerTheme from '@/moon/buyer_theme'

// ── 路由 ──────────────────────────────────────────────────────────────────
const route = useRoute()
const router = useRouter()
const mallId = Number(route.params.id)

// ── 状态 ──────────────────────────────────────────────────────────────────
interface ChatMessage {
  type: 'chat' | 'system'
  username?: string
  content: string
  created_at: string
}

const messages = ref<ChatMessage[]>([])
const onlineUsers = ref<string[]>([])
const inputText = ref('')
const msgListRef = ref<HTMLDivElement | null>(null)

type WsState = 'connecting' | 'open' | 'closed'
const wsState = ref<WsState>('connecting')
const wsStateLabel = computed(() => {
  if (wsState.value === 'open') return '已连接'
  if (wsState.value === 'connecting') return '连接中'
  return '已断开'
})

const currentUser = ref('')

let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let autoReconnect = true

// ── WebSocket ──────────────────────────────────────────────────────────────
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
  ws = new WebSocket(`ws://127.0.0.1:8000/api/ws/store_chat/${mallId}?token=${encodedToken}`)

  ws.onopen = () => {
    wsState.value = 'open'
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleServerMessage(data)
    } catch {
      // ignore malformed messages
    }
  }

  ws.onerror = () => {
    wsState.value = 'closed'
    ElMessage.error('WebSocket 连接出错')
  }

  ws.onclose = (e) => {
    wsState.value = 'closed'
    if (e.code === 4001) {
      ElMessage.error('Token 无效，请重新登录')
      autoReconnect = false
    } else if (e.code === 4003) {
      ElMessage.error('您没有权限访问该店铺聊天室')
      autoReconnect = false
    } else if (autoReconnect) {
      reconnectTimer = setTimeout(connect, 3000)
    }
  }
}

function handleServerMessage(data: any) {
  if (data.type === 'history') {
    messages.value = data.data || []
    scrollToBottom()
    return
  }

  if (data.type === 'system') {
    // 更新在线用户列表
    if (Array.isArray(data.online_users)) {
      onlineUsers.value = data.online_users
    }
    // 解析当前用户名（来自欢迎消息）
    if (data.content === '成功加入店铺聊天室' && data.username) {
      currentUser.value = data.username
    }
    messages.value.push({
      type: 'system',
      content: data.content,
      created_at: data.created_at,
    })
    scrollToBottom()
    return
  }

  if (data.type === 'chat') {
    messages.value.push({
      type: 'chat',
      username: data.username,
      content: data.content,
      created_at: data.created_at,
    })
    scrollToBottom()
  }
}

function sendMessage() {
  const content = inputText.value.trim()
  if (!content || wsState.value !== 'open') return
  if (content.length > 500) {
    ElMessage.warning('消息不能超过 500 个字符')
    return
  }

  ws?.send(JSON.stringify({ type: 'chat', content }))
  inputText.value = ''
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

function goBack() {
  disconnect()
  router.back()
}

// ── 辅助 ──────────────────────────────────────────────────────────────────
function scrollToBottom() {
  nextTick(() => {
    if (msgListRef.value) {
      msgListRef.value.scrollTop = msgListRef.value.scrollHeight
    }
  })
}

function formatTime(ts: string): string {
  if (!ts) return ''
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ts
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ── 生命周期 ──────────────────────────────────────────────────────────────
onMounted(() => {
  new BuyerTheme().initTheme()
  connect()
})

onBeforeUnmount(() => {
  disconnect()
})

// 新消息到来时自动滚底
watch(() => messages.value.length, () => {
  scrollToBottom()
})
</script>

<style scoped lang="scss">
.chat-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

/* ── Header ── */
.chat-header {
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

.status-tag {
  font-size: 11px;
}

/* ── Body ── */
.chat-body {
  flex: 1;
  overflow: hidden;
}

/* ── Aside ── */
.online-aside {
  border-right: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
}

.aside-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  padding-bottom: 8px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.online-count {
  margin-left: auto;
}

.online-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.online-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: 8px;
  transition: background 0.2s;

  &:hover {
    background: var(--el-fill-color-light);
  }

  &--self {
    background: rgba(102, 126, 234, 0.08);
  }
}

.online-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #67c23a;
  flex-shrink: 0;
}

.online-name {
  font-size: 13px;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.no-online {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  text-align: center;
  padding: 12px 0;
}

/* ── Main chat area ── */
.chat-main {
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

.msg-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  scroll-behavior: smooth;
}

/* ── Message rows ── */
.msg-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;

  &--self {
    flex-direction: row-reverse;
  }

  &--system {
    justify-content: center;
  }
}

/* 系统消息 */
.sys-msg {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  background: var(--el-fill-color-light);
  padding: 4px 12px;
  border-radius: 20px;

  .el-icon {
    font-size: 13px;
  }
}

/* 头像 */
.avatar-wrap {
  flex-shrink: 0;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;

  &--self {
    background: linear-gradient(135deg, #43e97b, #38f9d7);
  }
}

/* 气泡 */
.bubble-wrap {
  display: flex;
  flex-direction: column;
  max-width: 60%;

  &--self {
    align-items: flex-end;
  }

  &--other {
    align-items: flex-start;
  }
}

.msg-sender {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-bottom: 4px;
  padding-left: 4px;
}

.bubble {
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;

  &--other {
    background: var(--el-fill-color-light);
    color: var(--el-text-color-primary);
    border-bottom-left-radius: 4px;
  }

  &--self {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    border-bottom-right-radius: 4px;
  }
}

.msg-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-top: 4px;
  padding: 0 4px;

  &--self {
    text-align: right;
  }
}

/* ── 空状态 & 连接中 ── */
.empty-hint,
.connecting-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 0;
  color: var(--el-text-color-placeholder);
  font-size: 14px;
  margin: auto;

  .el-icon {
    opacity: 0.4;
  }

  p {
    margin: 0;
  }
}

/* ── 输入区域 ── */
.input-area {
  border-top: 1px solid var(--el-border-color);
  padding: 12px 20px;
  background: var(--el-bg-color);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.input-tip {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

/* ── 深色模式 ── */
html.dark {
  .bubble--other {
    background: var(--el-fill-color);
    color: var(--el-text-color-primary);
  }

  .sys-msg {
    background: var(--el-fill-color);
  }
}
</style>
