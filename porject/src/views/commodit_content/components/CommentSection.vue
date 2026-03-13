<template>
  <div class="comment-section">

    <!-- 顶栏 -->
    <div class="cs-header">
      <div class="cs-title-group">
        <span class="cs-icon-wrap"><el-icon><ChatDotRound /></el-icon></span>
        <h3 class="cs-title">用户评价</h3>
        <span v-if="total > 0" class="cs-total">{{ total }} 条</span>
      </div>
      <button v-if="isLoggedIn" class="write-btn" @click="showForm = !showForm">
        <el-icon><EditPen /></el-icon>
        {{ showForm ? '收起' : '写评价' }}
      </button>
      <el-tooltip v-else content="登录后才能发表评价" placement="top">
        <button class="write-btn disabled" disabled>写评价</button>
      </el-tooltip>
    </div>

    <!-- 评价表单 -->
    <transition name="expand">
      <div v-if="showForm && isLoggedIn" class="form-wrap">
        <div class="form-inner">
          <div class="form-rating-row">
            <span class="form-lbl">本次评分</span>
            <el-rate v-model="form.rating" :colors="['#F56C6C','#E6A23C','#67C23A']" />
            <span class="rate-desc">{{ rateDesc }}</span>
          </div>
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="4"
            placeholder="说说你对这款商品的看法，帮助更多买家做决策～"
            maxlength="500"
            show-word-limit
            resize="none"
            class="form-ta"
          />
          <div class="form-footer">
            <el-button size="small" @click="resetForm">取消</el-button>
            <el-button
              type="primary"
              size="small"
              class="submit-btn"
              :loading="submitting"
              :disabled="!form.content.trim()"
              @click="submitComment"
            >
              发布评价
            </el-button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 骨架屏 -->
    <div v-if="loading" class="comment-list">
      <div v-for="n in 3" :key="n" class="comment-card skeleton-card">
        <el-skeleton animated :rows="3" />
      </div>
    </div>

    <!-- 评论列表 -->
    <div v-else-if="comments.length" class="comment-list">
      <div v-for="c in comments" :key="c.id" class="comment-card">
        <div class="cc-left">
          <div class="avatar" :style="{ background: avatarColor(c.username) }">
            {{ c.username?.charAt(0)?.toUpperCase() || 'U' }}
          </div>
        </div>
        <div class="cc-body">
          <div class="cc-meta">
            <span class="cc-name">{{ c.username }}</span>
            <el-rate :model-value="c.rating" disabled size="small" class="cc-rate" />
          </div>
          <p class="cc-text">{{ c.content }}</p>
          <span class="cc-time">{{ formatTime(c.created_at) }}</span>
        </div>
      </div>

      <div v-if="total > pageSize" class="pagination-row">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="fetchComments"
        />
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-wrap">
      <div class="empty-icon">💬</div>
      <p class="empty-title">还没有人评价</p>
      <p class="empty-sub">抢占沙发，成为第一个评价的人！</p>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotRound, EditPen } from '@element-plus/icons-vue'
import axios from 'axios'

const props = defineProps<{ shoppingId: number; mallId: number }>()

interface Comment {
  id: string
  username: string
  rating: number
  content: string
  created_at: string
}

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

const isLoggedIn = computed(() => !!localStorage.getItem('buyer_access_token'))

const loading   = ref(false)
const submitting = ref(false)
const showForm  = ref(false)
const comments  = ref<Comment[]>([])
const total     = ref(0)
const currentPage = ref(1)
const pageSize  = 10

const form = reactive({ rating: 5, content: '' })

const rateDesc = computed(() => ['', '很差', '较差', '一般', '满意', '非常满意'][form.rating] ?? '')

const AVATAR_COLORS = [
  '#667eea','#764ba2','#f093fb','#4facfe','#43e97b',
  '#f7971e','#fda085','#96fbc4','#a1c4fd','#fbc2eb',
]
const avatarColor = (name: string) => {
  const idx = (name?.charCodeAt(0) ?? 0) % AVATAR_COLORS.length
  return AVATAR_COLORS[idx]
}

const formatTime = (s: string) => {
  if (!s) return ''
  const d = new Date(s)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

const resetForm = () => { form.rating = 5; form.content = ''; showForm.value = false }

const fetchComments = async (page = 1) => {
  loading.value = true
  try {
    const res = await Axios.get('/commodity_comments', { params: { shopping_id: props.shoppingId, page } })
    if (res.data.success) {
      comments.value = res.data.data || []
      total.value = res.data.total || 0
    }
  } catch { /* 静默 */ } finally { loading.value = false }
}

const submitComment = async () => {
  if (!form.content.trim()) return
  submitting.value = true
  try {
    const token = localStorage.getItem('buyer_access_token')
    const res = await Axios.post('/commodity_comment', null, {
      params: {
        shopping_id: props.shoppingId,
        mall_id: props.mallId,
        rating: form.rating,
        content: form.content.trim(),
      },
      headers: { 'access-token': token ?? '' },
    })
    if (res.data.success) {
      ElMessage.success('评价发布成功 🎉')
      resetForm()
      fetchComments(1)
    } else {
      ElMessage.warning(res.data.msg || '发布失败')
    }
  } catch { ElMessage.error('网络错误，请稍后重试') } finally { submitting.value = false }
}

onMounted(() => fetchComments(1))
</script>

<style scoped lang="scss">
.comment-section {
  border-radius: 20px;
  background: var(--el-bg-color);
  border: 1px solid var(--color-border);
  overflow: hidden;
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
}

/* ── 顶栏 ── */
.cs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-background-soft);
}

.cs-title-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cs-icon-wrap {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea22, #764ba222);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #667eea;
  font-size: 16px;
}

.cs-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-heading);
  margin: 0;
}

.cs-total {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  background: var(--el-fill-color);
  padding: 2px 8px;
  border-radius: 20px;
}

.write-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  border-radius: 8px;
  border: 1.5px solid #667eea;
  background: transparent;
  color: #667eea;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;

  &:hover { background: rgba(102,126,234,0.06); }
  &.disabled { border-color: var(--el-border-color); color: var(--el-text-color-placeholder); cursor: not-allowed; }
}

/* ── 表单 ── */
.form-wrap {
  border-bottom: 1px solid var(--color-border);
  overflow: hidden;
}

.form-inner {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  background: var(--color-background-soft);
}

.form-rating-row {
  display: flex;
  align-items: center;
  gap: 12px;

  .form-lbl { font-size: 13px; color: var(--el-text-color-secondary); }
  .rate-desc { font-size: 13px; color: #e6a23c; font-weight: 600; }
}

.form-ta :deep(.el-textarea__inner) {
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.75;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;

  .submit-btn {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border: none;
    color: #fff;
  }
}

/* ── 评论列表 ── */
.comment-list {
  display: flex;
  flex-direction: column;
}

.comment-card {
  display: flex;
  gap: 14px;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
  transition: background 0.15s;

  &:last-child { border-bottom: none; }
  &:hover { background: var(--color-background-soft); }

  &.skeleton-card { padding: 20px 24px; }
}

.cc-left { flex-shrink: 0; }

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0;
}

.cc-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cc-meta {
  display: flex;
  align-items: center;
  gap: 10px;

  .cc-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  .cc-rate :deep(.el-rate__icon) {
    font-size: 13px;
    margin-right: 1px;
  }
}

.cc-text {
  font-size: 14px;
  line-height: 1.75;
  color: var(--el-text-color-regular);
  margin: 0;
  word-break: break-word;
}

.cc-time {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.pagination-row {
  display: flex;
  justify-content: center;
  padding: 16px;
  border-top: 1px solid var(--color-border);
}

/* ── 空状态 ── */
.empty-wrap {
  padding: 60px 24px;
  text-align: center;

  .empty-icon { font-size: 48px; margin-bottom: 12px; line-height: 1; }
  .empty-title { font-size: 16px; font-weight: 700; color: var(--el-text-color-primary); margin: 0 0 6px; }
  .empty-sub   { font-size: 13px; color: var(--el-text-color-placeholder); margin: 0; }
}

/* ── 动画 ── */
.expand-enter-active, .expand-leave-active { transition: all 0.3s ease; overflow: hidden; }
.expand-enter-from, .expand-leave-to { opacity: 0; max-height: 0; }
.expand-enter-to, .expand-leave-from { opacity: 1; max-height: 400px; }
</style>
