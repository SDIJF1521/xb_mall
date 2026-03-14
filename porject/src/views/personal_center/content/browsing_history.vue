<template>
  <div class="history-container">
    <!-- 顶部栏 -->
    <div class="history-header">
      <span class="history-title">浏览历史</span>
      <el-button
        v-if="list.length > 0"
        type="danger"
        size="small"
        plain
        round
        :loading="clearing"
        @click="confirmClearAll"
      >
        清空全部
      </el-button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="history-loading">
      <el-skeleton :rows="4" animated />
    </div>

    <!-- 空状态 -->
    <el-empty v-else-if="list.length === 0" description="暂无浏览记录" />

    <!-- 记录列表 -->
    <div v-else>
      <div
        v-for="item in list"
        :key="item.shopping_id"
        class="history-item"
        :class="{ 'history-item--unavailable': !item.available }"
      >
        <!-- 商品图片 -->
        <div class="item-img" @click="goDetail(item)">
          <el-image
            v-if="item.img"
            :src="item.img.startsWith('data:') ? item.img : 'data:image/jpeg;base64,' + item.img"
            fit="cover"
            class="img"
          />
          <div v-else class="img img--placeholder">
            <el-icon size="28" color="#ccc"><Picture /></el-icon>
          </div>
          <div v-if="!item.available" class="item-img__mask">已下架</div>
        </div>

        <!-- 商品信息 -->
        <div class="item-info" @click="goDetail(item)">
          <div class="item-name">{{ item.name }}</div>
          <div class="item-meta">
            <span class="item-price" v-if="item.available">¥ {{ item.price.toFixed(2) }}</span>
            <span class="item-count">浏览 {{ item.browse_count }} 次</span>
          </div>
          <div class="item-time">最近浏览：{{ formatTime(item.last_browse_at) }}</div>
        </div>

        <!-- 删除按钮 -->
        <el-button
          class="item-delete"
          type="danger"
          link
          size="small"
          :loading="deletingId === item.shopping_id"
          @click.stop="deleteItem(item)"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>

      <!-- 分页 -->
      <div class="history-pagination">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          small
          background
          @current-change="fetchList"
        />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Picture, Delete } from '@element-plus/icons-vue'

defineOptions({ name: 'BrowsingHistory' })

const router = useRouter()
const token = localStorage.getItem('access_token') || ''

const Axios = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  headers: { 'access-token': token },
})

interface HistoryItem {
  shopping_id: number
  mall_id: number
  name: string
  img: string
  price: number
  type: string[]
  browse_count: number
  last_browse_at: string
  available: boolean
}

const list = ref<HistoryItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const clearing = ref(false)
const deletingId = ref<number | null>(null)

async function fetchList() {
  loading.value = true
  try {
    const res = await Axios.get('/browsing_history', { params: { page: page.value } })
    if (res.data.success) {
      list.value = res.data.data
      total.value = res.data.total
    } else {
      ElMessage.error(res.data.msg || '获取失败')
    }
  } catch {
    ElMessage.error('网络异常，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function deleteItem(item: HistoryItem) {
  deletingId.value = item.shopping_id
  try {
    const res = await Axios.delete('/browsing_history', {
      params: { shopping_id: item.shopping_id },
    })
    if (res.data.success) {
      ElMessage.success('已删除')
      await fetchList()
    } else {
      ElMessage.error(res.data.msg || '删除失败')
    }
  } catch {
    ElMessage.error('网络异常，请稍后重试')
  } finally {
    deletingId.value = null
  }
}

function confirmClearAll() {
  ElMessageBox.confirm('确定要清空所有浏览记录吗？', '提示', {
    confirmButtonText: '确定清空',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(clearAll)
}

async function clearAll() {
  clearing.value = true
  try {
    const res = await Axios.delete('/browsing_history/all')
    if (res.data.success) {
      ElMessage.success('已清空')
      list.value = []
      total.value = 0
      page.value = 1
    } else {
      ElMessage.error(res.data.msg || '清空失败')
    }
  } catch {
    ElMessage.error('网络异常，请稍后重试')
  } finally {
    clearing.value = false
  }
}

function goDetail(item: HistoryItem) {
  if (!item.available) return
  router.push(`/commodity/${item.mall_id}/${item.shopping_id}`)
}

function formatTime(iso: string): string {
  if (!iso) return '未知'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(fetchList)
</script>

<style scoped>
.history-container {
  width: 100%;
  max-width: 720px;
  padding: 20px 24px;
  box-sizing: border-box;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.history-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.history-loading {
  padding: 16px 0;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 8px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.15s;
  border-radius: 6px;
  cursor: pointer;
}

.history-item:hover {
  background: #fafafa;
}

.history-item--unavailable {
  opacity: 0.55;
  cursor: default;
}

.item-img {
  position: relative;
  flex-shrink: 0;
  width: 72px;
  height: 72px;
  border-radius: 6px;
  overflow: hidden;
  background: #f5f5f5;
}

.img {
  width: 100%;
  height: 100%;
  display: block;
}

.img--placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
}

.item-img__mask {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.item-price {
  font-size: 14px;
  color: #f56c6c;
  font-weight: 600;
}

.item-count {
  font-size: 12px;
  color: #909399;
}

.item-time {
  font-size: 12px;
  color: #b0b3bb;
}

.item-delete {
  flex-shrink: 0;
  margin-left: auto;
}

.history-pagination {
  display: flex;
  justify-content: center;
  padding-top: 20px;
}
</style>
