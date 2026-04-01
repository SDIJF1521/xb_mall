<template>
  <div class="my-comments">
    <h3 class="mc-title">我的评论</h3>

    <!-- 首次加载 -->
    <div v-if="initialLoading" class="mc-loading">
      <el-skeleton v-for="n in 3" :key="n" animated :rows="3" style="margin-bottom: 16px" />
    </div>

    <!-- 评论列表 -->
    <template v-else-if="comments.length">
      <div v-for="c in comments" :key="c.id" class="mc-card">
        <div class="mc-card-header">
          <div class="mc-order-info">
            <span class="mc-label">订单号</span>
            <span class="mc-value">{{ c.order_no }}</span>
          </div>
          <div class="mc-rating">
            <el-rate :model-value="c.rating" disabled size="small" />
          </div>
        </div>

        <p class="mc-content">{{ c.content }}</p>

        <!-- 评论图片 -->
        <div v-if="c.images?.length" class="mc-images">
          <el-image
            v-for="(img, idx) in c.images"
            :key="idx"
            :src="img"
            :preview-src-list="c.images"
            :initial-index="idx"
            fit="cover"
            class="mc-img-item"
            lazy
          />
        </div>

        <!-- 卖家回复 -->
        <div v-if="c.seller_reply" class="mc-reply">
          <span class="mc-reply-tag">卖家回复</span>
          <p class="mc-reply-text">{{ c.seller_reply.content }}</p>
          <span class="mc-reply-time">{{ formatTime(c.seller_reply.replied_at) }}</span>
        </div>

        <div class="mc-card-footer">
          <span class="mc-time">{{ formatTime(c.created_at) }}</span>
          <el-popconfirm
            title="确定要删除这条评论吗？"
            confirm-button-text="删除"
            cancel-button-text="取消"
            @confirm="deleteComment(c.id)"
          >
            <template #reference>
              <el-button type="danger" text size="small" :loading="deletingId === c.id">
                <el-icon><Delete /></el-icon> 删除
              </el-button>
            </template>
          </el-popconfirm>
        </div>
      </div>

      <!-- 加载更多触发器 -->
      <div ref="sentinelRef" class="mc-load-more-sentinel">
        <div v-if="loadingMore" class="mc-load-more">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>加载更多评论...</span>
        </div>
        <div v-else-if="noMore" class="mc-load-more mc-no-more">
          <span>— 已加载全部评论 —</span>
        </div>
      </div>
    </template>

    <!-- 空状态 -->
    <el-empty v-else-if="!initialLoading" description="暂无评论记录" :image-size="120" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Loading } from '@element-plus/icons-vue'
import axios from 'axios'

defineOptions({ name: 'ConterComment' })

interface SellerReply {
  content: string
  replied_at: string
  replied_by: string
}

interface UserComment {
  id: string
  shopping_id: number
  mall_id: number
  order_no: string
  rating: number
  content: string
  images: string[]
  created_at: string
  updated_at: string
  seller_reply: SellerReply | null
}

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const getHeaders = () => {
  const token = localStorage.getItem('access_token')
  return token ? { 'access-token': token } : {}
}

const initialLoading = ref(false)
const loadingMore    = ref(false)
const comments       = ref<UserComment[]>([])
const total          = ref(0)
const page           = ref(1)
const pageSize       = 10
const noMore         = computed(() => comments.value.length >= total.value && comments.value.length > 0)
const deletingId     = ref<string | null>(null)

const sentinelRef = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

const formatTime = (s: string) => {
  if (!s) return ''
  const d = new Date(s)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const fetchComments = async (p = 1, reset = false) => {
  if (reset) {
    initialLoading.value = true
  } else {
    loadingMore.value = true
  }
  try {
    const res = await Axios.get('/comment/user_list', {
      params: { page: p, page_size: pageSize },
      headers: getHeaders(),
    })
    if (res.data?.success) {
      const newData: UserComment[] = res.data.data || []
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
    ElMessage.error('网络错误')
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
      page.value = 1
      total.value = 0
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

onMounted(() => fetchComments(1, true))

onBeforeUnmount(() => {
  if (observer) observer.disconnect()
})
</script>

<style scoped>
.my-comments {
  width: 100%;
  max-width: 800px;
  padding: 20px;
}

.mc-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 20px;
  color: var(--el-text-color-primary);
}

.mc-loading {
  padding: 10px 0;
}

.mc-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 12px;
  transition: box-shadow 0.2s;
}

.mc-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.mc-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.mc-order-info {
  display: flex;
  gap: 8px;
  align-items: center;
}

.mc-label {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.mc-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.mc-content {
  font-size: 14px;
  line-height: 1.75;
  color: var(--el-text-color-primary);
  margin: 0 0 8px;
  word-break: break-word;
}

.mc-images {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.mc-img-item {
  width: 72px;
  height: 72px;
  border-radius: 8px;
  cursor: pointer;
  object-fit: cover;
}

.mc-reply {
  margin: 8px 0;
  padding: 10px 14px;
  background: var(--el-fill-color-extra-light);
  border-radius: 8px;
  border-left: 3px solid #667eea;
}

.mc-reply-tag {
  font-size: 12px;
  font-weight: 600;
  color: #667eea;
  background: rgba(102,126,234,0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

.mc-reply-text {
  font-size: 13px;
  color: var(--el-text-color-regular);
  margin: 6px 0 4px;
  line-height: 1.6;
}

.mc-reply-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.mc-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid var(--el-border-color-extra-light);
}

.mc-time {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.mc-load-more-sentinel {
  min-height: 1px;
}

.mc-load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.mc-no-more {
  color: var(--el-text-color-placeholder);
  font-size: 12px;
  padding: 16px 0;
}
</style>
