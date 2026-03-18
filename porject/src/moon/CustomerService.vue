<template>
  <div class="cs-root">
    <!-- 悬浮按钮（可通过 showFab=false 隐藏） -->
    <transition name="bounce">
      <button v-if="!open && props.showFab !== false" class="cs-fab" title="联系客服" @click="openChat">
        <el-icon :size="26"><Service /></el-icon>
        <span class="fab-label">客服</span>
        <span v-if="unreadCount > 0" class="fab-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
      </button>
    </transition>

    <!-- 聊天面板 -->
    <transition name="panel-slide">
      <div v-if="open" class="cs-panel">

        <!-- 头部 -->
        <div class="panel-header">
          <div class="header-left">
            <div class="store-avatar">
              <el-icon :size="18"><Service /></el-icon>
            </div>
            <div class="store-info">
              <span class="store-name">在线客服</span>
              <span class="store-status">
                <span
                  class="status-dot"
                  :class="wsState === 'open' ? 'dot--online' : 'dot--offline'"
                />
                {{ wsState === 'open' ? '已连接' : wsState === 'connecting' ? '连接中...' : '已断开' }}
              </span>
            </div>
          </div>
          <div class="header-actions">
            <el-tooltip v-if="wsState === 'closed'" content="重新连接" placement="bottom">
              <button class="icon-btn" @click="reconnect">
                <el-icon><Refresh /></el-icon>
              </button>
            </el-tooltip>
            <button class="close-btn" @click="open = false">
              <el-icon><Close /></el-icon>
            </button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div ref="msgListRef" class="msg-list">
          <!-- 连接中 / 已断开 占位 -->
          <div v-if="wsState !== 'open' && messages.length === 0" class="conn-hint">
            <el-icon v-if="wsState === 'connecting'" class="is-loading" :size="28"><Loading /></el-icon>
            <el-icon v-else :size="28"><WarningFilled /></el-icon>
            <p>{{ wsState === 'connecting' ? '正在连接客服...' : '连接已断开，请点击右上角重新连接' }}</p>
          </div>

          <template v-for="(msg, idx) in messages" :key="idx">
            <!-- 系统消息 -->
            <div v-if="msg.sender_type === 'system'" class="sys-msg">
              <el-icon><InfoFilled /></el-icon>
              {{ msg.content }}
            </div>

            <!-- 用户消息（右侧） -->
            <div v-else-if="msg.sender_type === 'user'" class="msg-row right">
              <div class="msg-col">
                <!-- 商品卡片 -->
                <div v-if="msg.message_type === 'product_card' && msg.product_info" class="product-card user-card">
                  <div class="pc-header">
                    <el-icon><Goods /></el-icon>
                    <span>商品咨询</span>
                  </div>
                  <div class="pc-body">
                    <img
                      v-if="msg.product_info.img"
                      :src="msg.product_info.img"
                      class="pc-img"
                      alt="商品图片"
                    />
                    <div class="pc-info">
                      <div class="pc-name">{{ msg.product_info.name }}</div>
                      <div v-if="msg.product_info.spec" class="pc-spec">{{ msg.product_info.spec }}</div>
                      <div class="pc-price">¥{{ msg.product_info.price }}</div>
                    </div>
                  </div>
                  <a class="pc-link" :href="msg.product_info.url" target="_blank">查看商品详情 →</a>
                </div>
                <!-- 普通文本 -->
                <div v-else class="msg-bubble user-bubble">{{ msg.content }}</div>
                <div class="msg-time">{{ msg.created_at }}</div>
              </div>
              <div class="msg-avatar user-avatar">我</div>
            </div>

            <!-- 客服消息（左侧） -->
            <div v-else class="msg-row left">
              <div class="msg-avatar cs-avatar"><el-icon><Service /></el-icon></div>
              <div class="msg-col">
                <div class="msg-sender">客服</div>
                <div class="msg-bubble cs-bubble">{{ msg.content }}</div>
                <div class="msg-time">{{ msg.created_at }}</div>
              </div>
            </div>
          </template>
        </div>

        <!-- 商品快捷发送栏（仅商品详情页） -->
        <div v-if="props.commodity" class="product-quick-bar">
          <div class="pq-info">
            <el-icon><Goods /></el-icon>
            <span class="pq-name">{{ props.commodity.name }}</span>
          </div>
          <div v-if="props.commodity.specification_list?.length" class="pq-spec-row">
            <span class="pq-label">规格：</span>
            <div class="pq-spec-list">
              <button
                v-for="(spec, idx) in props.commodity.specification_list"
                :key="idx"
                class="pq-spec-btn"
                :class="{ 'pq-spec-btn--active': selectedSpecIdx === idx }"
                :disabled="spec.stock === 0"
                @click="selectedSpecIdx = idx"
              >
                {{ spec.specs?.join(' · ') || '默认' }}
              </button>
            </div>
          </div>
          <el-button
            size="small"
            type="primary"
            :disabled="wsState !== 'open'"
            @click="sendProductCard"
          >
            <el-icon><Promotion /></el-icon>
            发送商品到对话
          </el-button>
        </div>

        <!-- 输入区 -->
        <div class="input-area">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            resize="none"
            placeholder="输入您的问题..."
            :disabled="wsState !== 'open'"
            class="msg-input"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <button
            class="send-btn"
            :class="{ active: inputText.trim() && wsState === 'open' }"
            :disabled="!inputText.trim() || wsState !== 'open'"
            @click="sendMessage"
          >
            <el-icon><Promotion /></el-icon>
          </button>
        </div>
        <p class="input-tip">Enter 发送 · Shift+Enter 换行</p>

      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onBeforeUnmount, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import {
  Service, Close, Promotion, Loading, Refresh,
  InfoFilled, Goods, WarningFilled,
} from '@element-plus/icons-vue'

interface Spec {
  specs: string[]
  price: number
  stock: number
}

interface Commodity {
  shopping_id: number
  mall_id: number
  name: string
  price: number
  img_list?: string[]
  specification_list?: Spec[]
}

interface CsMessage {
  sender_type: 'user' | 'seller' | 'system'
  sender_name?: string
  content: string
  message_type?: 'text' | 'product_card'
  product_info?: {
    name: string
    spec: string
    url: string
    price: string
    img?: string
  }
  created_at: string
}

const props = defineProps<{
  mallId: number
  shoppingId?: number
  commodity?: Commodity | null
  /** 是否显示悬浮球按钮，默认 true；设为 false 时只渲染面板，由外部调用 openChat() 打开 */
  showFab?: boolean
}>()

const open = ref(false)
const inputText = ref('')
const messages = ref<CsMessage[]>([])
const msgListRef = ref<HTMLElement | null>(null)
const selectedSpecIdx = ref(0)
const unreadCount = ref(0)

type WsState = 'connecting' | 'open' | 'closed'
const wsState = ref<WsState>('closed')

let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let autoReconnect = true

// ── WebSocket ────────────────────────────────────────────────────────────────

function getToken(): string {
  return localStorage.getItem('access_token') || ''
}

function connect() {
  const token = getToken()
  if (!token) return

  wsState.value = 'connecting'
  const encodedToken = encodeURIComponent(token)
  ws = new WebSocket(
    `ws://127.0.0.1:8000/api/ws/customer_service/${props.mallId}?token=${encodedToken}&client_type=user`
  )

  ws.onopen = () => {
    wsState.value = 'open'
  }

  ws.onmessage = (event) => {
    try {
      handleServerMessage(JSON.parse(event.data))
    } catch {
      // ignore malformed
    }
  }

  ws.onerror = () => {
    wsState.value = 'closed'
  }

  ws.onclose = (e) => {
    wsState.value = 'closed'
    if (e.code === 4001 || e.code === 4002) {
      autoReconnect = false
    } else if (autoReconnect) {
      reconnectTimer = setTimeout(connect, 4000)
    }
  }
}

function handleServerMessage(data: any) {
  if (data.type === 'history') {
    messages.value = (data.data || []).map(normalizeMsg)
    scrollBottom()
    return
  }
  if (data.type === 'system') {
    messages.value.push({
      sender_type: 'system',
      content: data.content,
      created_at: formatTime(data.created_at),
    })
    scrollBottom()
    return
  }
  if (data.type === 'chat') {
    messages.value.push(normalizeMsg(data))
    if (!open.value && data.sender_type === 'seller') {
      unreadCount.value++
    }
    scrollBottom()
  }
}

function normalizeMsg(m: any): CsMessage {
  return {
    sender_type: m.sender_type || 'seller',
    sender_name: m.sender_name,
    content: m.content || '',
    message_type: m.message_type || 'text',
    product_info: m.product_info,
    created_at: formatTime(m.created_at),
  }
}

function sendMessage() {
  const content = inputText.value.trim()
  if (!content || wsState.value !== 'open') return
  if (content.length > 500) {
    ElMessage.warning('消息不能超过 500 字')
    return
  }
  ws?.send(JSON.stringify({ type: 'chat', content, message_type: 'text' }))
  inputText.value = ''
}

function sendProductCard() {
  if (!props.commodity || wsState.value !== 'open') return

  const spec = props.commodity.specification_list?.[selectedSpecIdx.value]
  const specText = spec?.specs?.join(' · ') || '默认规格'
  const price = spec?.price ?? props.commodity.price ?? 0

  const rawImg = props.commodity.img_list?.[0] ?? ''
  const img = rawImg
    ? (rawImg.startsWith('data:') ? rawImg : `data:image/jpeg;base64,${rawImg}`)
    : ''

  const productInfo = {
    name: props.commodity.name,
    spec: specText,
    url: `${window.location.origin}/commodity/${props.mallId}/${props.commodity.shopping_id}`,
    price: String(price),
    img,
  }

  ws?.send(JSON.stringify({
    type: 'chat',
    content: props.commodity.name,
    message_type: 'product_card',
    product_info: productInfo,
  }))
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

// ── 面板开关 ──────────────────────────────────────────────────────────────────

function openChat() {
  open.value = true
  unreadCount.value = 0
  if (wsState.value === 'closed') {
    const token = getToken()
    if (!token) {
      ElMessage.warning('请先登录后再联系客服')
      return
    }
    autoReconnect = true
    connect()
  }
  scrollBottom()
}

// ── 辅助 ─────────────────────────────────────────────────────────────────────

async function scrollBottom() {
  await nextTick()
  if (msgListRef.value) {
    msgListRef.value.scrollTop = msgListRef.value.scrollHeight
  }
}

function formatTime(ts: string): string {
  if (!ts) return ''
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ts
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ── 初始未读数（页面加载时从 API 获取）───────────────────────────────────────────

async function fetchInitialUnread() {
  const token = getToken()
  if (!token || !props.mallId) return
  try {
    const res = await axios.get(
      `http://127.0.0.1:8000/api/cs_unread_count?role=user&mall_id=${props.mallId}`,
      { headers: { 'access-token': token } }
    )
    if (res.data?.current && typeof res.data.unread_count === 'number') {
      unreadCount.value = res.data.unread_count
    }
  } catch {
    // ignore
  }
}

// ── 生命周期 ──────────────────────────────────────────────────────────────────

onMounted(() => {
  fetchInitialUnread()
})

onBeforeUnmount(() => {
  disconnect()
})

// ── 暴露给父组件 ──────────────────────────────────────────────────────────────

defineExpose({ openChat })
</script>

<style scoped lang="scss">
/* ── 根容器 ── */
.cs-root {
  position: fixed;
  bottom: 32px;
  right: 32px;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

/* ── 悬浮按钮 ── */
.cs-fab {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.5);
  transition: transform 0.25s, box-shadow 0.25s;

  &:hover {
    transform: translateY(-4px) scale(1.07);
    box-shadow: 0 14px 32px rgba(102, 126, 234, 0.6);
  }

  &:active { transform: scale(0.94); }

  .fab-label {
    font-size: 10px;
    font-weight: 600;
    line-height: 1;
  }
}

.fab-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  border-radius: 9px;
  background: #f56c6c;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ── 聊天面板 ── */
.cs-panel {
  width: 360px;
  max-height: 580px;
  border-radius: 20px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 头部 */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.store-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
}

.store-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.store-name {
  font-size: 15px;
  font-weight: 700;
  line-height: 1;
}

.store-status {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  opacity: 0.9;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;

  &.dot--online {
    background: #67c23a;
    animation: pulseDot 1.6s ease-in-out infinite;
  }

  &.dot--offline { background: rgba(255,255,255,0.5); }
}

@keyframes pulseDot {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.icon-btn,
.close-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;

  &:hover { background: rgba(255, 255, 255, 0.38); }
}

/* 消息列表 */
.msg-list {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  scroll-behavior: smooth;
  min-height: 0;

  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-thumb {
    background: var(--el-border-color);
    border-radius: 4px;
  }
}

.conn-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 40px 0;
  color: var(--el-text-color-placeholder);
  font-size: 13px;
  margin: auto;

  p { margin: 0; text-align: center; }
}

.sys-msg {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  background: var(--el-fill-color-light);
  padding: 4px 12px;
  border-radius: 20px;
  align-self: center;

  .el-icon { font-size: 12px; }
}

.msg-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;

  &.right { flex-direction: row-reverse; }
}

.msg-col {
  display: flex;
  flex-direction: column;
  max-width: 240px;

  .right & { align-items: flex-end; }
  .left &  { align-items: flex-start; }
}

.msg-sender {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-bottom: 3px;
}

.msg-time {
  font-size: 10px;
  color: var(--el-text-color-placeholder);
  margin-top: 3px;
}

.msg-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;

  &.cs-avatar {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
  }

  &.user-avatar {
    background: linear-gradient(135deg, #f093fb, #f5576c);
    color: #fff;
  }
}

.msg-bubble {
  padding: 9px 13px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.65;
  word-break: break-word;

  &.cs-bubble {
    background: var(--el-fill-color-light);
    color: var(--el-text-color-primary);
    border: 1px solid var(--el-border-color-light);
    border-bottom-left-radius: 4px;
  }

  &.user-bubble {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    border-bottom-right-radius: 4px;
  }
}

/* 商品卡片 */
.product-card {
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 240px;
  border-bottom-right-radius: 4px;

  &.user-card {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
  }

  .pc-header {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 10px;
    font-weight: 600;
    opacity: 0.85;
  }

  .pc-body {
    display: flex;
    gap: 10px;
    align-items: flex-start;
  }

  .pc-img {
    width: 64px;
    height: 64px;
    border-radius: 8px;
    object-fit: cover;
    flex-shrink: 0;
    background: rgba(255, 255, 255, 0.15);
  }

  .pc-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 0;
  }

  .pc-name {
    font-size: 13px;
    font-weight: 600;
    line-height: 1.4;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  .pc-spec {
    font-size: 11px;
    opacity: 0.85;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .pc-price { font-size: 14px; font-weight: 700; }

  .pc-link {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.9);
    text-decoration: underline;
    cursor: pointer;
    text-align: right;
  }
}

/* 商品快捷发送栏 */
.product-quick-bar {
  border-top: 1px solid var(--el-border-color-light);
  padding: 8px 12px;
  background: var(--el-fill-color-extra-light);
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
}

.pq-info {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.pq-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 260px;
}

.pq-spec-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pq-label {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  flex-shrink: 0;
}

.pq-spec-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.pq-spec-btn {
  padding: 2px 8px;
  border-radius: 12px;
  border: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.18s;

  &--active {
    border-color: #667eea;
    background: rgba(102, 126, 234, 0.1);
    color: #667eea;
  }

  &:disabled { opacity: 0.4; cursor: not-allowed; }
}

/* 输入区 */
.input-area {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 8px 12px 4px;
  border-top: 1px solid var(--el-border-color-light);
  flex-shrink: 0;

  .msg-input {
    flex: 1;

    :deep(.el-textarea__inner) {
      border-radius: 12px;
      font-size: 13px;
      line-height: 1.6;
    }
  }
}

.send-btn {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  border: none;
  background: var(--el-fill-color);
  color: var(--el-text-color-placeholder);
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;

  &.active {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }

  &:disabled { cursor: not-allowed; opacity: 0.7; }
}

.input-tip {
  font-size: 10px;
  color: var(--el-text-color-placeholder);
  text-align: right;
  padding: 2px 14px 6px;
  margin: 0;
  flex-shrink: 0;
}

/* ── 动画 ── */
.bounce-enter-active { animation: bounceIn 0.38s ease; }
.bounce-leave-active { animation: bounceIn 0.22s ease reverse; }

@keyframes bounceIn {
  0%   { transform: scale(0.5); opacity: 0; }
  65%  { transform: scale(1.1); }
  100% { transform: scale(1); opacity: 1; }
}

.panel-slide-enter-active { animation: slideUp 0.28s cubic-bezier(0.34, 1.56, 0.64, 1); }
.panel-slide-leave-active { animation: slideUp 0.18s ease reverse; }

@keyframes slideUp {
  from { opacity: 0; transform: translateY(16px) scale(0.96); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
</style>
