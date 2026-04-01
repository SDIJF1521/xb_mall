<template>
  <el-container>
    <el-container>
      <BuyerNavigation />
      <el-container>
        <el-header>
          <BuyerHead />
        </el-header>
        <el-main>
          <div class="cm-container">
            <h2 class="page-title">评论管理中心</h2>
            <p class="page-subtitle">查看和回复买家评论，提升店铺服务质量</p>

            <!-- 店铺选择（主账号多店铺时显示） -->
            <div v-if="isOwner && storeList.length > 1" class="cm-store-selector">
              <span class="cm-store-label">当前店铺：</span>
              <el-select
                v-model="selectedMallId"
                placeholder="选择店铺"
                style="width: 240px"
                @change="onStoreChange"
              >
                <el-option
                  v-for="s in storeList"
                  :key="s.id"
                  :label="s.mall_name"
                  :value="s.id"
                />
              </el-select>
            </div>

            <!-- 筛选栏 -->
            <div class="cm-filters">
              <div class="cm-tabs">
                <span
                  v-for="tab in ratingTabs"
                  :key="tab.key"
                  class="cm-tab"
                  :class="{ active: ratingFilter === tab.key }"
                  @click="setRatingFilter(tab.key)"
                >{{ tab.label }}</span>
              </div>
              <div class="cm-reply-filter">
                <el-select
                  v-model="replyFilter"
                  placeholder="回复状态"
                  clearable
                  style="width: 140px"
                  @change="onFilterChange"
                >
                  <el-option label="全部状态" value="" />
                  <el-option label="未回复" value="unreplied" />
                  <el-option label="已回复" value="replied" />
                </el-select>
              </div>
            </div>

            <!-- 首次加载中 -->
            <div v-if="initialLoading" class="cm-loading">
              <el-icon class="is-loading" :size="32"><Loading /></el-icon>
              <p>加载中...</p>
            </div>

            <!-- 评论列表 -->
            <template v-else-if="comments.length">
              <div v-for="c in comments" :key="c.id" class="cm-card">
                <div class="cm-card-header">
                  <div class="cm-user-info">
                    <img
                      v-if="c.avatar"
                      class="cm-avatar cm-avatar-img"
                      :src="'data:image/jpeg;base64,' + c.avatar"
                      alt="avatar"
                    />
                    <div v-else class="cm-avatar" :style="{ background: avatarColor(c.username) }">
                      {{ c.username?.charAt(0)?.toUpperCase() || 'U' }}
                    </div>
                    <div>
                      <div class="cm-username">{{ c.username }}</div>
                      <div class="cm-meta-row">
                        <span class="cm-order-no">订单 {{ c.order_no }}</span>
                        <span class="cm-dot">·</span>
                        <span class="cm-time">{{ formatTime(c.created_at) }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="cm-rating-badge" :class="ratingClass(c.rating)">
                    <el-rate :model-value="c.rating" disabled size="small" />
                    <span class="cm-rating-text">{{ ratingText(c.rating) }}</span>
                  </div>
                </div>

                <p class="cm-content">{{ c.content }}</p>

                <!-- 评论图片 -->
                <div v-if="c.images?.length" class="cm-images">
                  <el-image
                    v-for="(img, idx) in c.images"
                    :key="idx"
                    :src="img"
                    :preview-src-list="c.images"
                    :initial-index="idx"
                    fit="cover"
                    class="cm-img-item"
                    lazy
                  />
                </div>

                <!-- 已有回复 -->
                <div v-if="c.seller_reply" class="cm-reply-box">
                  <div class="cm-reply-header">
                    <span class="cm-reply-tag">已回复</span>
                    <span class="cm-reply-by">{{ c.seller_reply.replied_by }}</span>
                    <span class="cm-reply-time">{{ formatTime(c.seller_reply.replied_at) }}</span>
                  </div>
                  <p class="cm-reply-text">{{ c.seller_reply.content }}</p>
                </div>

                <!-- 回复操作 -->
                <div v-else class="cm-reply-action">
                  <template v-if="replyingId === c.id">
                    <el-input
                      v-model="replyContent"
                      type="textarea"
                      :rows="3"
                      placeholder="输入回复内容..."
                      maxlength="500"
                      show-word-limit
                      resize="none"
                    />
                    <div class="cm-reply-btns">
                      <el-button size="small" @click="cancelReply">取消</el-button>
                      <el-button
                        type="primary"
                        size="small"
                        :loading="replySubmitting"
                        :disabled="!replyContent.trim()"
                        @click="submitReply(c.id)"
                      >发送回复</el-button>
                    </div>
                  </template>
                  <el-button
                    v-else
                    type="primary"
                    text
                    size="small"
                    @click="startReply(c.id)"
                  >
                    <el-icon><ChatDotRound /></el-icon> 回复
                  </el-button>
                </div>
              </div>

              <!-- 加载更多触发器 -->
              <div ref="sentinelRef" class="cm-load-more-sentinel">
                <div v-if="loadingMore" class="cm-load-more">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  <span>加载更多评论...</span>
                </div>
                <div v-else-if="noMore" class="cm-load-more cm-no-more">
                  <span>— 已加载全部评论 —</span>
                </div>
              </div>
            </template>

            <!-- 空状态 -->
            <el-empty v-else-if="!initialLoading" description="暂无评论" :image-size="120" />
          </div>
        </el-main>
      </el-container>
    </el-container>
    <el-footer class="footer-content">版权所有 ©[xb商城]，保留所有权利。</el-footer>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Loading, ChatDotRound } from '@element-plus/icons-vue'
import BuyerNavigation from '@/moon/buyer_navigation.vue'
import BuyerHead from '@/moon/buyer_head.vue'
import BuyerTheme from '@/moon/buyer_theme'

defineOptions({ name: 'BuyerCommentManage' })

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const getHeaders = () => {
  const token = localStorage.getItem('buyer_access_token')
  return token ? { 'Access-Token': token } : {}
}

function decodeTokenPayload(token: string): Record<string, any> | null {
  try {
    const parts = token.split('.')
    if (parts.length < 2) return null
    const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(payload))
  } catch {
    return null
  }
}

// ── 店铺选择 ──
const isOwner = ref(false)
const storeList = ref<{ id: number; mall_name: string }[]>([])
const selectedMallId = ref<number | null>(null)

async function loadStoreList() {
  const token = localStorage.getItem('buyer_access_token')
  if (!token) return
  const payload = decodeTokenPayload(token)
  if (!payload) return

  if (String(payload.station) === '1') {
    isOwner.value = true
    try {
      const form = new FormData()
      form.append('token', token)
      const res = await Axios.post('/get_mall_name', form)
      if (res.data?.mall_name?.length) {
        storeList.value = res.data.mall_name
        selectedMallId.value = storeList.value[0].id
      }
    } catch { /* ignore */ }
  } else if (String(payload.station) === '2') {
    selectedMallId.value = payload.mall_id ? Number(payload.mall_id) : null
  }
}

function onStoreChange() {
  resetAndFetch()
}

// ── 筛选 ──
const ratingTabs = [
  { key: '', label: '全部' },
  { key: 'good', label: '好评' },
  { key: 'average', label: '中评' },
  { key: 'bad', label: '差评' },
]
const ratingFilter = ref('')
const replyFilter = ref('')

function setRatingFilter(key: string) {
  ratingFilter.value = key
  resetAndFetch()
}

function onFilterChange() {
  resetAndFetch()
}

function resetAndFetch() {
  comments.value = []
  page.value = 1
  total.value = 0
  fetchComments(1, true)
}

// ── 评论数据 ──
interface SellerReply {
  content: string
  replied_at: string
  replied_by: string
}

interface SellerComment {
  id: string
  shopping_id: number
  order_no: string
  username: string
  avatar: string
  rating: number
  content: string
  images: string[]
  created_at: string
  seller_reply: SellerReply | null
}

const initialLoading = ref(false)
const loadingMore    = ref(false)
const comments       = ref<SellerComment[]>([])
const total          = ref(0)
const page           = ref(1)
const pageSize       = 10
const noMore         = computed(() => comments.value.length >= total.value && comments.value.length > 0)

const sentinelRef = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

// ── 回复 ──
const replyingId      = ref<string | null>(null)
const replyContent    = ref('')
const replySubmitting = ref(false)

function startReply(commentId: string) {
  replyingId.value = commentId
  replyContent.value = ''
}

function cancelReply() {
  replyingId.value = null
  replyContent.value = ''
}

const AVATAR_COLORS = [
  '#667eea','#764ba2','#f093fb','#4facfe','#43e97b',
  '#f7971e','#fda085','#96fbc4','#a1c4fd','#fbc2eb',
]
const avatarColor = (name: string) => {
  const idx = (name?.charCodeAt(0) ?? 0) % AVATAR_COLORS.length
  return AVATAR_COLORS[idx]
}

function ratingText(r: number) {
  if (r >= 4) return '好评'
  if (r === 3) return '中评'
  return '差评'
}

function ratingClass(r: number) {
  if (r >= 4) return 'rating-good'
  if (r === 3) return 'rating-average'
  return 'rating-bad'
}

const formatTime = (s: string) => {
  if (!s) return ''
  const d = new Date(s)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

async function fetchComments(p = 1, reset = false) {
  if (!selectedMallId.value) return
  if (reset) {
    initialLoading.value = true
  } else {
    loadingMore.value = true
  }
  try {
    const params: Record<string, any> = {
      mall_id: selectedMallId.value,
      page: p,
      page_size: pageSize,
    }
    if (ratingFilter.value) params.rating_type = ratingFilter.value
    if (replyFilter.value) params.reply_status = replyFilter.value

    const res = await Axios.get('/comment/seller_list', {
      params,
      headers: getHeaders(),
    })
    if (res.data?.success) {
      const newData: SellerComment[] = res.data.data || []
      if (reset) {
        comments.value = newData
      } else {
        comments.value.push(...newData)
      }
      total.value = res.data.total || 0
      page.value = p
      await nextTick()
      setupObserver()
    } else {
      ElMessage.error(res.data?.msg || '获取评论失败')
    }
  } catch {
    ElMessage.error('请求失败，请检查网络')
  } finally {
    initialLoading.value = false
    loadingMore.value = false
  }
}

function loadNextPage() {
  if (loadingMore.value || initialLoading.value || noMore.value) return
  fetchComments(page.value + 1)
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

async function submitReply(commentId: string) {
  if (!replyContent.value.trim() || !selectedMallId.value) return
  replySubmitting.value = true
  try {
    const fd = new FormData()
    fd.append('comment_id', commentId)
    fd.append('reply_content', replyContent.value.trim())
    fd.append('mall_id', String(selectedMallId.value))

    const res = await Axios.post('/comment/seller_reply', fd, { headers: getHeaders() })
    if (res.data?.success) {
      ElMessage.success('回复成功')
      cancelReply()
      resetAndFetch()
    } else {
      ElMessage.error(res.data?.msg || '回复失败')
    }
  } catch {
    ElMessage.error('网络错误')
  } finally {
    replySubmitting.value = false
  }
}

onMounted(async () => {
  new BuyerTheme().initTheme()
  await loadStoreList()
  if (selectedMallId.value) fetchComments(1, true)
})

onBeforeUnmount(() => {
  if (observer) observer.disconnect()
})
</script>

<style scoped>
.el-header {
  border-bottom: 1px solid #514d4d;
  padding-bottom: 10px;
  margin-bottom: 10px;
}

.cm-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  text-align: center;
  font-size: 32px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
}

.page-subtitle {
  text-align: center;
  font-size: 16px;
  color: #7f8c8d;
  margin-bottom: 32px;
}

.cm-store-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 10px 16px;
  background: var(--el-bg-color);
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.cm-store-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  white-space: nowrap;
}

/* ── 筛选栏 ── */
.cm-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 12px;
  flex-wrap: wrap;
}

.cm-tabs {
  display: flex;
  gap: 4px;
  background: var(--el-bg-color);
  border-radius: 10px;
  padding: 4px;
}

.cm-tab {
  padding: 8px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  color: var(--el-text-color-regular);
}

.cm-tab:hover { background: var(--el-fill-color-light); }
.cm-tab.active {
  background: var(--el-color-primary);
  color: #fff;
  font-weight: 500;
}

/* ── 加载 ── */
.cm-loading {
  text-align: center;
  padding: 60px 0;
  color: var(--el-text-color-secondary);
}

/* ── 评论卡片 ── */
.cm-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 18px 22px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  transition: box-shadow 0.2s;
}

.cm-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

.cm-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 12px;
}

.cm-user-info {
  display: flex;
  gap: 12px;
  align-items: center;
}

.cm-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  flex-shrink: 0;
}

.cm-avatar-img {
  object-fit: cover;
}

.cm-username {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.cm-meta-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin-top: 2px;
}

.cm-dot { color: var(--el-border-color); }

.cm-rating-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.rating-good { background: #f0f9eb; color: #67c23a; }
.rating-average { background: #fdf6ec; color: #e6a23c; }
.rating-bad { background: #fef0f0; color: #f56c6c; }

.cm-content {
  font-size: 14px;
  line-height: 1.75;
  color: var(--el-text-color-primary);
  margin: 0 0 10px;
  word-break: break-word;
}

.cm-images {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.cm-img-item {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  cursor: pointer;
  object-fit: cover;
}

/* ── 已有回复 ── */
.cm-reply-box {
  padding: 12px 16px;
  background: var(--el-fill-color-extra-light);
  border-radius: 10px;
  border-left: 3px solid #667eea;
}

.cm-reply-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.cm-reply-tag {
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  background: #67c23a;
  padding: 2px 8px;
  border-radius: 4px;
}

.cm-reply-by {
  font-size: 12px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.cm-reply-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.cm-reply-text {
  font-size: 13px;
  color: var(--el-text-color-regular);
  margin: 0;
  line-height: 1.6;
}

/* ── 回复操作 ── */
.cm-reply-action {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--el-border-color-extra-light);
}

.cm-reply-btns {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

/* ── 懒加载 ── */
.cm-load-more-sentinel {
  min-height: 1px;
}

.cm-load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.cm-no-more {
  color: var(--el-text-color-placeholder);
  font-size: 12px;
  padding: 16px 0;
}

.footer-content {
  text-align: center;
  color: darkgray;
}
</style>
