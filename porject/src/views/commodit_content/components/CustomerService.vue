<template>
  <div class="cs-root">
    <!-- 悬浮按钮 -->
    <transition name="bounce">
      <button v-if="!open" class="cs-fab" title="联系客服" @click="openChat">
        <el-icon :size="26"><Service /></el-icon>
        <span class="fab-label">客服</span>
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
                <span class="status-dot" />
                随时为您服务
              </span>
            </div>
          </div>
          <button class="close-btn" @click="open = false">
            <el-icon><Close /></el-icon>
          </button>
        </div>

        <!-- 消息列表 -->
        <div ref="msgListRef" class="msg-list">
          <!-- 欢迎语 -->
          <div class="msg-row left">
            <div class="msg-avatar cs-avatar"><el-icon><Service /></el-icon></div>
            <div class="msg-bubble cs-bubble">您好！欢迎咨询，请问有什么可以帮您的？😊</div>
          </div>

          <!-- 快捷问题（首次） -->
          <div v-if="messages.length === 0" class="quick-block">
            <p class="quick-title">您可能想问：</p>
            <button
              v-for="q in quickQuestions"
              :key="q"
              class="quick-btn"
              @click="sendQuick(q)"
            >{{ q }}</button>
          </div>

          <!-- 对话消息 -->
          <template v-for="(msg, idx) in messages" :key="idx">
            <div v-if="msg.role === 'user'" class="msg-row right">
              <div class="msg-bubble user-bubble">{{ msg.content }}</div>
              <div class="msg-avatar user-avatar">我</div>
            </div>
            <div v-else class="msg-row left">
              <div class="msg-avatar cs-avatar"><el-icon><Service /></el-icon></div>
              <div class="msg-bubble cs-bubble">
                <span v-if="msg.loading" class="typing-dots">
                  <span /><span /><span />
                </span>
                <span v-else>{{ msg.content }}</span>
              </div>
            </div>
          </template>
        </div>

        <!-- 快捷条（有消息后显示） -->
        <div v-if="messages.length > 0" class="quick-strip">
          <button
            v-for="q in quickQuestions.slice(0, 3)"
            :key="q"
            class="strip-btn"
            @click="sendQuick(q)"
          >{{ q }}</button>
        </div>

        <!-- 输入区 -->
        <div class="input-area">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            resize="none"
            placeholder="请输入您的问题..."
            class="msg-input"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <button
            class="send-btn"
            :class="{ active: inputText.trim() }"
            :disabled="!inputText.trim() || replying"
            @click="sendMessage"
          >
            <el-icon v-if="!replying"><Promotion /></el-icon>
            <el-icon v-else class="is-loading"><Loading /></el-icon>
          </button>
        </div>
        <p class="input-tip">Enter 发送 · Shift+Enter 换行</p>

      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { Service, Close, Promotion, Loading } from '@element-plus/icons-vue'

interface Msg {
  role: 'user' | 'cs'
  content: string
  loading?: boolean
}

const open      = ref(false)
const inputText = ref('')
const replying  = ref(false)
const messages  = ref<Msg[]>([])
const msgListRef = ref<HTMLElement | null>(null)

const quickQuestions = [
  '这个商品还有货吗？',
  '支持哪些快递？',
  '可以退换货吗？',
  '多久能发货？',
  '有优惠活动吗？',
]

const autoReply: Record<string, string> = {
  '这个商品还有货吗？':
    '您好，该商品目前有库存，可以放心下单！如需了解具体规格的剩余数量，请查看规格参数页。',
  '支持哪些快递？':
    '我们支持顺丰、圆通、中通、韵达等主流快递，会根据您所在地区选择最优方案发货。',
  '可以退换货吗？':
    '支持7天无理由退换货，商品须保持原状未使用。退货运费由买家承担，质量问题除外。',
  '多久能发货？':
    '下单后48小时内安排发货，节假日可能延迟1-2天，敬请谅解。',
  '有优惠活动吗？':
    '您可以关注店铺获取最新优惠信息，也可在商城首页查看当期促销活动～',
}

const defaultReply =
  '您的问题已收到！由于您的问题较为特殊，建议您前往"我的订单"页面提交售后申请，或拨打官方客服热线，我们会在第一时间为您处理。'

const scrollBottom = async () => {
  await nextTick()
  if (msgListRef.value) msgListRef.value.scrollTop = msgListRef.value.scrollHeight
}

const openChat = () => {
  open.value = true
  scrollBottom()
}

const sendQuick = (q: string) => {
  inputText.value = q
  sendMessage()
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || replying.value) return

  inputText.value = ''
  messages.value.push({ role: 'user', content: text })
  await scrollBottom()

  // 打字动画占位
  const csIdx = messages.value.length
  messages.value.push({ role: 'cs', content: '', loading: true })
  await scrollBottom()

  replying.value = true
  await new Promise(r => setTimeout(r, 800))

  const reply = autoReply[text] ?? defaultReply
  messages.value[csIdx] = { role: 'cs', content: reply }
  replying.value = false
  await scrollBottom()
}
</script>

<style scoped lang="scss">
/* ── 根容器（固定悬浮） ── */
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

/* ── 聊天面板 ── */
.cs-panel {
  width: 360px;
  height: 520px;
  border-radius: 20px;
  background: var(--el-bg-color);
  border: 1px solid var(--color-border);
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
  gap: 2px;

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
    opacity: 0.85;

    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #67c23a;
      animation: pulseDot 1.6s ease-in-out infinite;
    }
  }
}

@keyframes pulseDot {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}

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
  padding: 16px 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  scroll-behavior: smooth;

  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-thumb {
    background: var(--el-border-color);
    border-radius: 4px;
  }
}

.msg-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;

  &.right { flex-direction: row-reverse; }
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
  max-width: 240px;
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 13px;
  line-height: 1.7;
  word-break: break-word;

  &.cs-bubble {
    background: var(--color-background-soft);
    color: var(--el-text-color-primary);
    border: 1px solid var(--color-border);
    border-bottom-left-radius: 4px;
  }

  &.user-bubble {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    border-bottom-right-radius: 4px;
  }
}

/* 打字动画 */
.typing-dots {
  display: flex;
  align-items: center;
  gap: 4px;
  height: 16px;

  span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--el-text-color-placeholder);
    animation: typingBounce 1.2s ease-in-out infinite;

    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0);   opacity: 0.4; }
  30%            { transform: translateY(-6px); opacity: 1; }
}

/* 快捷问题首屏 */
.quick-block {
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin-top: 2px;

  .quick-title {
    font-size: 11px;
    color: var(--el-text-color-placeholder);
    margin: 0 0 2px 38px;
  }
}

.quick-btn {
  align-self: flex-start;
  margin-left: 38px;
  padding: 6px 14px;
  border-radius: 20px;
  border: 1.5px solid rgba(102, 126, 234, 0.4);
  background: rgba(102, 126, 234, 0.06);
  color: #667eea;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.18s;

  &:hover {
    background: rgba(102, 126, 234, 0.14);
    border-color: #667eea;
  }
}

/* 快捷条（对话后底部） */
.quick-strip {
  display: flex;
  gap: 6px;
  padding: 6px 12px;
  border-top: 1px solid var(--color-border);
  overflow-x: auto;
  flex-shrink: 0;

  &::-webkit-scrollbar { display: none; }
}

.strip-btn {
  flex-shrink: 0;
  padding: 4px 12px;
  border-radius: 16px;
  border: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  color: var(--el-text-color-secondary);
  font-size: 11px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.18s;

  &:hover {
    border-color: #667eea;
    color: #667eea;
    background: rgba(102, 126, 234, 0.06);
  }
}

/* 输入区 */
.input-area {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 10px 12px 6px;
  border-top: 1px solid var(--color-border);
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
  width: 40px;
  height: 40px;
  border-radius: 12px;
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
  padding: 2px 14px 8px;
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
