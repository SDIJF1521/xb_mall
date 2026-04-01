<template>
  <div class="comment-section">

    <!-- 顶栏 -->
    <div class="cs-header">
      <div class="cs-title-group">
        <span class="cs-icon-wrap"><el-icon><ChatDotRound /></el-icon></span>
        <h3 class="cs-title">用户评价</h3>
        <span v-if="statistics.total > 0" class="cs-total">{{ statistics.total }} 条</span>
      </div>
      <button
        v-if="isLoggedIn && commentable"
        class="write-btn"
        @click="showForm = !showForm"
      >
        <el-icon><EditPen /></el-icon>
        {{ showForm ? '收起' : '写评价' }}
      </button>
      <el-tooltip v-else-if="!isLoggedIn" content="登录后才能发表评价" placement="top">
        <button class="write-btn disabled" disabled>写评价</button>
      </el-tooltip>
      <el-tooltip v-else :content="commentableMsg" placement="top">
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
          <!-- 图片上传 -->
          <div class="form-upload-row">
            <el-upload
              v-model:file-list="form.imageFiles"
              list-type="picture-card"
              :auto-upload="false"
              accept="image/*"
              :limit="9"
              :on-exceed="() => ElMessage.warning('最多上传9张图片')"
            >
              <el-icon><Plus /></el-icon>
              <template #tip>
                <div class="upload-tip">最多9张，每张不超过5MB</div>
              </template>
            </el-upload>
          </div>
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

    <!-- 筛选 Tabs -->
    <div v-if="statistics.total > 0" class="filter-tabs">
      <span
        class="filter-tab"
        :class="{ active: !ratingType }"
        @click="setFilter(null)"
      >全部 {{ statistics.total }}</span>
      <span
        class="filter-tab good"
        :class="{ active: ratingType === 'good' }"
        @click="setFilter('good')"
      >好评 {{ statistics.good }}</span>
      <span
        class="filter-tab average"
        :class="{ active: ratingType === 'average' }"
        @click="setFilter('average')"
      >中评 {{ statistics.average }}</span>
      <span
        class="filter-tab bad"
        :class="{ active: ratingType === 'bad' }"
        @click="setFilter('bad')"
      >差评 {{ statistics.bad }}</span>
    </div>

    <!-- 首次加载骨架屏 -->
    <div v-if="initialLoading" class="comment-list">
      <div v-for="n in 3" :key="n" class="comment-card skeleton-card">
        <el-skeleton animated :rows="3" />
      </div>
    </div>

    <!-- 评论列表 -->
    <div v-else-if="comments.length" class="comment-list">
      <div v-for="c in comments" :key="c.id" class="comment-card">
        <div class="cc-left">
          <img
            v-if="c.avatar"
            class="avatar avatar-img"
            :src="'data:image/jpeg;base64,' + c.avatar"
            alt="avatar"
          />
          <div v-else class="avatar" :style="{ background: avatarColor(c.username) }">
            {{ c.username?.charAt(0)?.toUpperCase() || 'U' }}
          </div>
        </div>
        <div class="cc-body">
          <div class="cc-meta">
            <span class="cc-name">
              {{ c.username }}
              <span v-if="isOwnComment(c.username)" class="cc-own-tag">我的</span>
            </span>
            <el-rate :model-value="c.rating" disabled size="small" class="cc-rate" />
          </div>
          <p class="cc-text">{{ c.content }}</p>
          <!-- 评论图片 -->
          <div v-if="c.images?.length" class="cc-images">
            <el-image
              v-for="(img, idx) in c.images"
              :key="idx"
              :src="img"
              :preview-src-list="c.images"
              :initial-index="idx"
              fit="cover"
              class="cc-img-item"
              lazy
            />
          </div>
          <div class="cc-footer">
            <span class="cc-time">{{ formatTime(c.created_at) }}</span>
            <el-popconfirm
              v-if="isOwnComment(c.username)"
              title="确定要删除这条评论吗？"
              confirm-button-text="删除"
              cancel-button-text="取消"
              @confirm="deleteComment(c.id)"
            >
              <template #reference>
                <el-button
                  type="danger"
                  text
                  size="small"
                  :loading="deletingId === c.id"
                >
                  <el-icon><Delete /></el-icon> 删除
                </el-button>
              </template>
            </el-popconfirm>
          </div>
          <!-- 卖家回复 -->
          <div v-if="c.seller_reply" class="cc-reply">
            <span class="cc-reply-tag">卖家回复</span>
            <p class="cc-reply-text">{{ c.seller_reply.content }}</p>
            <span class="cc-reply-time">{{ formatTime(c.seller_reply.replied_at) }}</span>
          </div>
        </div>
      </div>

      <!-- 加载更多触发器 -->
      <div ref="sentinelRef" class="load-more-sentinel">
        <div v-if="loadingMore" class="load-more-indicator">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>加载更多评论...</span>
        </div>
        <div v-else-if="noMore" class="load-more-indicator no-more">
          <span>— 已加载全部评论 —</span>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!initialLoading" class="empty-wrap">
      <div class="empty-icon"><el-icon :size="48"><ChatDotRound /></el-icon></div>
      <p class="empty-title">还没有人评价</p>
      <p class="empty-sub">抢占沙发，成为第一个评价的人！</p>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotRound, EditPen, Plus, Loading, Delete } from '@element-plus/icons-vue'
import type { UploadUserFile } from 'element-plus'
import axios from 'axios'

const props = defineProps<{ shoppingId: number; mallId: number }>()

interface SellerReply {
  content: string
  replied_at: string
  replied_by: string
}

interface Comment {
  id: string
  username: string
  avatar: string
  rating: number
  content: string
  images: string[]
  created_at: string
  seller_reply: SellerReply | null
}

interface Statistics {
  total: number
  good: number
  average: number
  bad: number
}

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

const isLoggedIn = computed(() => !!localStorage.getItem('access_token'))
const getHeaders = () => {
  const token = localStorage.getItem('access_token')
  return token ? { 'access-token': token } : {}
}

const currentUsername = ref('')

function parseTokenUsername() {
  try {
    const token = localStorage.getItem('access_token')
    if (!token) return
    const parts = token.split('.')
    if (parts.length < 2) return
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
    currentUsername.value = payload.user || ''
  } catch { /* ignore */ }
}

const isOwnComment = (username: string) => {
  return currentUsername.value && username === currentUsername.value
}

const initialLoading = ref(false)
const loadingMore    = ref(false)
const submitting     = ref(false)
const showForm       = ref(false)
const commentable    = ref(false)
const commentableMsg = ref('请先购买并确认收货后再评论')
const comments       = ref<Comment[]>([])
const total          = ref(0)
const currentPage    = ref(1)
const pageSize       = 10
const noMore         = computed(() => comments.value.length >= total.value && comments.value.length > 0)
const ratingType     = ref<string | null>(null)
const statistics     = ref<Statistics>({ total: 0, good: 0, average: 0, bad: 0 })

const deletingId     = ref<string | null>(null)

const sentinelRef = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

const form = reactive({
  rating: 5,
  content: '',
  imageFiles: [] as UploadUserFile[],
})

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

const resetForm = () => {
  form.rating = 5
  form.content = ''
  form.imageFiles = []
  showForm.value = false
}

const setFilter = (type: string | null) => {
  ratingType.value = type
  comments.value = []
  currentPage.value = 1
  total.value = 0
  fetchComments(1, true)
}

const checkCommentable = async () => {
  if (!isLoggedIn.value) return
  try {
    const res = await Axios.get('/comment/check', {
      params: { shopping_id: props.shoppingId, mall_id: props.mallId },
      headers: getHeaders(),
    })
    commentable.value = !!res.data?.commentable
    commentableMsg.value = res.data?.msg || '暂时无法评论'
  } catch { /* ignore */ }
}

const fetchComments = async (page = 1, reset = false) => {
  if (reset) {
    initialLoading.value = true
  } else {
    loadingMore.value = true
  }
  try {
    const params: Record<string, any> = {
      shopping_id: props.shoppingId,
      mall_id: props.mallId,
      page,
      page_size: pageSize,
    }
    if (ratingType.value) params.rating_type = ratingType.value
    const res = await Axios.get('/comment/list', { params })
    if (res.data?.success) {
      const newData: Comment[] = res.data.data || []
      if (reset) {
        comments.value = newData
      } else {
        comments.value.push(...newData)
      }
      total.value = res.data.total || 0
      currentPage.value = page
      if (res.data.statistics) {
        statistics.value = res.data.statistics
      }
      await nextTick()
      setupObserver()
    }
  } catch { /* ignore */ } finally {
    initialLoading.value = false
    loadingMore.value = false
  }
}

function loadNextPage() {
  if (loadingMore.value || initialLoading.value || noMore.value) return
  fetchComments(currentPage.value + 1)
}

function setupObserver() {
  if (observer) observer.disconnect()
  if (!sentinelRef.value || noMore.value) return
  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting) loadNextPage()
    },
    { rootMargin: '200px' }
  )
  observer.observe(sentinelRef.value)
}

watch(sentinelRef, () => setupObserver())

const deleteComment = async (commentId: string) => {
  deletingId.value = commentId
  try {
    const res = await Axios.delete('/comment/delete', {
      params: { comment_id: commentId },
      headers: getHeaders(),
    })
    if (res.data?.success) {
      ElMessage.success('评论已删除')
      comments.value = []
      currentPage.value = 1
      total.value = 0
      await checkCommentable()
      fetchComments(1, true)
    } else {
      ElMessage.error(res.data?.msg || '删除失败')
    }
  } catch {
    ElMessage.error('网络错误')
  } finally {
    deletingId.value = null
  }
}

const submitComment = async () => {
  if (!form.content.trim()) return
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('shopping_id', String(props.shoppingId))
    fd.append('mall_id', String(props.mallId))
    fd.append('rating', String(form.rating))
    fd.append('content', form.content.trim())
    for (const file of form.imageFiles) {
      if (file.raw) fd.append('images', file.raw)
    }
    const res = await Axios.post('/comment/create', fd, { headers: getHeaders() })
    if (res.data?.success) {
      ElMessage.success('评价发布成功')
      resetForm()
      await checkCommentable()
      comments.value = []
      currentPage.value = 1
      fetchComments(1, true)
    } else {
      ElMessage.warning(res.data?.msg || '发布失败')
    }
  } catch { ElMessage.error('网络错误，请稍后重试') } finally { submitting.value = false }
}

onMounted(() => {
  parseTokenUsername()
  fetchComments(1, true)
  checkCommentable()
})

onBeforeUnmount(() => {
  if (observer) observer.disconnect()
})
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

/* ── 筛选 Tabs ── */
.filter-tabs {
  display: flex;
  gap: 0;
  padding: 0 24px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-background-soft);
}

.filter-tab {
  padding: 12px 20px;
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;

  &:hover { color: var(--el-text-color-primary); }
  &.active { color: #667eea; border-bottom-color: #667eea; font-weight: 600; }
  &.good.active { color: #67c23a; border-bottom-color: #67c23a; }
  &.average.active { color: #e6a23c; border-bottom-color: #e6a23c; }
  &.bad.active { color: #f56c6c; border-bottom-color: #f56c6c; }
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

.form-upload-row {
  :deep(.el-upload--picture-card) {
    width: 80px;
    height: 80px;
    border-radius: 8px;
  }
  :deep(.el-upload-list__item) {
    width: 80px;
    height: 80px;
    border-radius: 8px;
  }
}

.upload-tip {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
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

.avatar-img {
  object-fit: cover;
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

.cc-images {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.cc-img-item {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  cursor: pointer;
  object-fit: cover;
}

.cc-own-tag {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  color: #667eea;
  background: rgba(102,126,234,0.1);
  padding: 1px 6px;
  border-radius: 4px;
  margin-left: 6px;
  vertical-align: middle;
}

.cc-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.cc-time {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

/* ── 卖家回复 ── */
.cc-reply {
  margin-top: 8px;
  padding: 10px 14px;
  background: var(--el-fill-color-extra-light);
  border-radius: 10px;
  border-left: 3px solid #667eea;
}

.cc-reply-tag {
  font-size: 12px;
  font-weight: 600;
  color: #667eea;
  background: rgba(102,126,234,0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

.cc-reply-text {
  font-size: 13px;
  color: var(--el-text-color-regular);
  margin: 6px 0 4px;
  line-height: 1.6;
}

.cc-reply-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.load-more-sentinel {
  min-height: 1px;
}

.load-more-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px 24px;
  font-size: 13px;
  color: var(--el-text-color-secondary);

  &.no-more {
    color: var(--el-text-color-placeholder);
    font-size: 12px;
    padding: 16px 24px;
  }
}

/* ── 空状态 ── */
.empty-wrap {
  padding: 60px 24px;
  text-align: center;

  .empty-icon { color: var(--el-text-color-placeholder); margin-bottom: 12px; line-height: 1; }
  .empty-title { font-size: 16px; font-weight: 700; color: var(--el-text-color-primary); margin: 0 0 6px; }
  .empty-sub   { font-size: 13px; color: var(--el-text-color-placeholder); margin: 0; }
}

/* ── 动画 ── */
.expand-enter-active, .expand-leave-active { transition: all 0.3s ease; overflow: hidden; }
.expand-enter-from, .expand-leave-to { opacity: 0; max-height: 0; }
.expand-enter-to, .expand-leave-from { opacity: 1; max-height: 600px; }
</style>
