<template>
  <div class="chat-window">
    <!-- 顶部用户信息栏 -->
    <div class="cw-header">
      <template v-if="props.sessionId">
        <div class="cw-user-info">
          <div class="cw-avatar">{{ props.sessionId.slice(0, 1).toUpperCase() }}</div>
          <div class="cw-user-meta">
            <span class="cw-username">{{ props.sessionId }}</span>
            <span class="cw-online-tag" :class="props.isOnline ? 'online' : 'offline'">
              <span class="online-dot" />
              {{ props.isOnline ? '在线' : '离线' }}
            </span>
          </div>
        </div>
      </template>
      <div v-else class="cw-placeholder-title">
        <el-icon><ChatDotRound /></el-icon>
        <span>请从左侧选择一个用户开始对话</span>
      </div>
    </div>

    <!-- 消息区 -->
    <div ref="msgListRef" class="cw-msg-list">

      <!-- 未选中会话时的空状态 -->
      <div v-if="!props.sessionId" class="cw-empty">
        <el-icon :size="56"><ChatDotRound /></el-icon>
        <p>选择一个用户会话开始客服工作</p>
      </div>

      <!-- 加载历史消息中 -->
      <div v-else-if="props.historyLoading" class="cw-loading">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <p>加载历史记录中...</p>
      </div>

      <template v-else>
        <div v-if="props.messages.length === 0" class="cw-empty">
          <el-icon :size="48"><ChatRound /></el-icon>
          <p>暂无聊天记录，等待用户发起咨询</p>
        </div>

        <div
          v-for="(msg, idx) in props.messages"
          :key="idx"
          class="cw-msg-row"
          :class="{
            'cw-msg-row--self': msg.sender_type === 'seller',
            'cw-msg-row--system': msg.sender_type === 'system',
          }"
        >
          <!-- 系统消息 -->
          <div v-if="msg.sender_type === 'system'" class="cw-sys-msg">
            <el-icon><InfoFilled /></el-icon>
            {{ msg.content }}
          </div>

          <!-- 用户消息（左侧） -->
          <template v-else-if="msg.sender_type === 'user'">
            <div class="cw-avatar-wrap">
              <div class="cw-bubble-avatar user-avatar">
                {{ (msg.sender_name || '用').slice(0, 1).toUpperCase() }}
              </div>
            </div>
            <div class="cw-bubble-col">
              <div class="cw-sender-name">{{ msg.sender_name }}</div>
              <!-- 商品卡片 -->
              <div v-if="msg.message_type === 'product_card' && msg.product_info" class="cw-product-card">
                <div class="cpc-header">
                  <el-icon><Goods /></el-icon>
                  <span>商品咨询</span>
                </div>
                <div class="cpc-body">
                  <img
                    v-if="msg.product_info.img"
                    :src="msg.product_info.img"
                    class="cpc-img"
                    alt="商品图片"
                  />
                  <div class="cpc-info">
                    <div class="cpc-name">{{ msg.product_info.name }}</div>
                    <div v-if="msg.product_info.spec" class="cpc-spec">{{ msg.product_info.spec }}</div>
                    <div class="cpc-price">¥{{ msg.product_info.price }}</div>
                  </div>
                </div>
                <a class="cpc-link" :href="msg.product_info.url" target="_blank">查看商品详情 →</a>
              </div>
              <!-- 文本 -->
              <div v-else class="cw-bubble user-bubble">{{ msg.content }}</div>
              <div class="cw-time">{{ msg.created_at }}</div>
            </div>
          </template>

          <!-- 客服消息（右侧） -->
          <template v-else-if="msg.sender_type === 'seller'">
            <div class="cw-bubble-col cw-bubble-col--self">
              <!-- 退款链接卡片 -->
              <div v-if="msg.message_type === 'refund_link' && msg.refund_info" class="cw-refund-card cw-refund-card--self">
                <div class="cw-refund-card__icon">💰</div>
                <div class="cw-refund-card__body">
                  <div class="cw-refund-card__title">退款快捷链接</div>
                  <div class="cw-refund-card__order">订单号：{{ msg.refund_info.order_no }}</div>
                </div>
              </div>
              <div v-else class="cw-bubble seller-bubble">{{ msg.content }}</div>
              <div class="cw-time cw-time--self">{{ msg.created_at }}</div>
            </div>
            <div class="cw-avatar-wrap">
              <div class="cw-bubble-avatar seller-avatar">客</div>
            </div>
          </template>
        </div>
      </template>
    </div>

    <!-- 输入区 -->
    <div class="cw-input-area" :class="{ disabled: !props.sessionId }">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="3"
        resize="none"
        :placeholder="props.sessionId ? '输入回复内容，Enter 发送...' : '请先选择用户会话'"
        :disabled="!props.sessionId || props.wsState !== 'open'"
        @keydown.enter.exact.prevent="handleSend"
      />
      <div class="cw-input-footer">
        <span class="cw-char-count">{{ inputText.length }}/500</span>
        <el-button
          :disabled="!props.sessionId || props.wsState !== 'open'"
          @click="openRefundLinkDialog"
          size="small"
        >
          退款链接
        </el-button>
        <el-button
          type="primary"
          :icon="Promotion"
          :disabled="!props.sessionId || !inputText.trim() || props.wsState !== 'open'"
          @click="handleSend"
        >
          发送
        </el-button>
      </div>
    </div>

    <!-- 退款链接弹窗 -->
    <el-dialog v-model="refundLinkDialogVisible" title="发送退款快捷链接" width="400px" append-to-body>
      <el-input v-model="refundOrderNo" placeholder="请输入订单号" clearable />
      <p style="margin-top:8px;font-size:12px;color:var(--el-text-color-secondary);">
        用户收到链接后可直接点击申请退款。
      </p>
      <template #footer>
        <el-button @click="refundLinkDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!refundOrderNo.trim()" @click="sendRefundLink">发送</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import {
  ChatDotRound, ChatRound, Loading, InfoFilled,
  Goods, Promotion,
} from '@element-plus/icons-vue'

export interface CsMsg {
  sender_type: 'user' | 'seller' | 'system'
  sender_name?: string
  content: string
  message_type?: 'text' | 'product_card' | 'refund_link'
  product_info?: {
    name: string
    spec: string
    url: string
    price: string
    img?: string
  }
  refund_info?: {
    order_no: string
  }
  created_at: string
}

const props = defineProps<{
  sessionId: string
  isOnline: boolean
  messages: CsMsg[]
  historyLoading: boolean
  wsState: 'connecting' | 'open' | 'closed'
}>()

const emit = defineEmits<{
  (e: 'send', content: string): void
  (e: 'sendRefundLink', orderNo: string): void
}>()

const inputText = ref('')
const msgListRef = ref<HTMLDivElement | null>(null)
const refundLinkDialogVisible = ref(false)
const refundOrderNo = ref('')

const scrollToBottom = () => {
  nextTick(() => {
    if (msgListRef.value) {
      msgListRef.value.scrollTop = msgListRef.value.scrollHeight
    }
  })
}

const handleSend = () => {
  const content = inputText.value.trim()
  if (!content) return
  emit('send', content)
  inputText.value = ''
}

const openRefundLinkDialog = () => {
  refundOrderNo.value = ''
  refundLinkDialogVisible.value = true
}

const sendRefundLink = () => {
  const no = refundOrderNo.value.trim()
  if (!no) return
  emit('sendRefundLink', no)
  refundLinkDialogVisible.value = false
  refundOrderNo.value = ''
}

watch(() => props.messages.length, () => {
  scrollToBottom()
})

watch(() => props.sessionId, () => {
  scrollToBottom()
})
</script>

<style scoped lang="scss">
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--el-bg-color-page);
}

/* 头部 */
.cw-header {
  height: 56px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  flex-shrink: 0;
}

.cw-user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cw-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cw-user-meta {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.cw-username {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.cw-online-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;

  &.online  { color: #67c23a; }
  &.offline { color: var(--el-text-color-placeholder); }

  .online-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
  }
}

.cw-placeholder-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-placeholder);
  font-size: 14px;
}

/* 消息区 */
.cw-msg-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  scroll-behavior: smooth;

  &::-webkit-scrollbar { width: 6px; }
  &::-webkit-scrollbar-thumb {
    background: var(--el-border-color);
    border-radius: 4px;
  }
}

.cw-empty,
.cw-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin: auto;
  color: var(--el-text-color-placeholder);
  font-size: 14px;

  p { margin: 0; }
}

/* 消息行 */
.cw-msg-row {
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

.cw-sys-msg {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  background: var(--el-fill-color-light);
  padding: 4px 12px;
  border-radius: 20px;
}

.cw-avatar-wrap { flex-shrink: 0; }

.cw-bubble-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;

  &.user-avatar {
    background: linear-gradient(135deg, #f093fb, #f5576c);
  }

  &.seller-avatar {
    background: linear-gradient(135deg, #43e97b, #38f9d7);
    color: #333;
  }
}

.cw-bubble-col {
  display: flex;
  flex-direction: column;
  max-width: 55%;

  &--self { align-items: flex-end; }
}

.cw-sender-name {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-bottom: 4px;
  padding-left: 4px;
}

.cw-bubble {
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;

  &.user-bubble {
    background: var(--el-fill-color-light);
    color: var(--el-text-color-primary);
    border: 1px solid var(--el-border-color-light);
    border-bottom-left-radius: 4px;
  }

  &.seller-bubble {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    border-bottom-right-radius: 4px;
  }
}

.cw-time {
  font-size: 10px;
  color: var(--el-text-color-placeholder);
  margin-top: 4px;
  padding-left: 4px;

  &--self {
    text-align: right;
    padding-right: 4px;
  }
}

/* 商品卡片 */
.cw-product-card {
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  border-bottom-left-radius: 4px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 260px;
  font-size: 12px;

  .cpc-header {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 10px;
    font-weight: 600;
    color: #667eea;
  }

  .cpc-body {
    display: flex;
    gap: 10px;
    align-items: flex-start;
  }

  .cpc-img {
    width: 68px;
    height: 68px;
    border-radius: 8px;
    object-fit: cover;
    flex-shrink: 0;
    border: 1px solid var(--el-border-color-light);
    background: var(--el-fill-color);
  }

  .cpc-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
  }

  .cpc-name {
    font-size: 13px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    line-height: 1.4;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  .cpc-spec {
    font-size: 11px;
    color: var(--el-text-color-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .cpc-price {
    font-size: 14px;
    font-weight: 700;
    color: #f56c6c;
  }

  .cpc-link {
    font-size: 11px;
    color: #667eea;
    text-decoration: underline;
    cursor: pointer;
    text-align: right;
  }
}

/* 输入区 */
.cw-input-area {
  border-top: 1px solid var(--el-border-color);
  padding: 12px 20px;
  background: var(--el-bg-color);
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;

  &.disabled {
    opacity: 0.6;
    pointer-events: none;
  }
}

.cw-input-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.cw-char-count {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.cw-refund-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  background: linear-gradient(135deg, #fff7ed 0%, #fef3c7 100%);
  border: 1px solid #fbbf24;
  max-width: 280px;
  cursor: pointer;

  &--self {
    margin-left: auto;
  }

  &__icon {
    font-size: 24px;
    flex-shrink: 0;
  }

  &__body {
    flex: 1;
    min-width: 0;
  }

  &__title {
    font-size: 13px;
    font-weight: 600;
    color: #92400e;
  }

  &__order {
    font-size: 11px;
    color: #b45309;
    margin-top: 2px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
