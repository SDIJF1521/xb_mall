<template>
  <div class="fav-container">
    <!-- 顶部栏 -->
    <div class="fav-header">
      <span class="fav-title">我的收藏</span>
      <div class="fav-toolbar">
        <el-input
          v-model="searchKw"
          placeholder="搜索收藏..."
          clearable
          size="small"
          style="width: 180px"
          @keyup.enter="doSearch"
          @clear="doSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 类型切换 -->
    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="商品" name="commodity" />
      <el-tab-pane label="店铺" name="store" />
    </el-tabs>

    <!-- 加载中 -->
    <div v-if="loading" class="fav-loading">
      <el-skeleton :rows="4" animated />
    </div>

    <!-- 空状态 -->
    <el-empty v-else-if="list.length === 0" description="暂无收藏" />

    <!-- 列表 -->
    <div v-else>
      <div
        v-for="item in list"
        :key="item.id"
        class="fav-item"
        :class="{ 'fav-item--unavailable': !item.available }"
      >
        <!-- 图片 -->
        <div class="item-img" @click="goDetail(item)">
          <el-image
            v-if="item.img"
            :src="item.img.startsWith('data:') ? item.img : 'data:image/jpeg;base64,' + item.img"
            fit="cover"
            class="img"
          />
          <div v-else class="img img--placeholder">
            <el-icon size="28" color="#ccc">
              <component :is="item.type === 'store' ? 'Shop' : 'Picture'" />
            </el-icon>
          </div>
          <div v-if="!item.available" class="item-img__mask">
            {{ item.type === 'store' ? '已关闭' : '已下架' }}
          </div>
        </div>

        <!-- 信息 -->
        <div class="item-info" @click="goDetail(item)">
          <div class="item-name">
            <el-tag v-if="item.type === 'store'" size="small" type="warning" style="margin-right: 6px">店铺</el-tag>
            <span>{{ item.name }}</span>
          </div>
          <div class="item-meta">
            <span v-if="item.type === 'commodity' && item.available" class="item-price">¥ {{ Number(item.price).toFixed(2) }}</span>
            <span v-if="item.type === 'store' && item.info" class="item-desc">{{ item.info }}</span>
          </div>
          <div class="item-time">收藏于：{{ formatTime(item.created_at) }}</div>
        </div>

        <!-- 取消收藏 -->
        <el-button
          class="item-delete"
          type="danger"
          link
          size="small"
          :loading="removingId === item.id"
          @click.stop="removeItem(item)"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>

      <!-- 分页 -->
      <div class="fav-pagination">
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
import { Search, Picture, Delete, Shop } from '@element-plus/icons-vue'

defineOptions({ name: 'CenterCollect' })

const router = useRouter()
const token = localStorage.getItem('access_token') || ''

const Axios = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  headers: { 'access-token': token },
})

interface FavItem {
  id: number
  type: 'commodity' | 'store'
  mall_id: number
  shopping_id: number | null
  name: string
  img: string
  price: number
  info?: string
  available: boolean
  created_at: string
}

const list = ref<FavItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const removingId = ref<number | null>(null)
const searchKw = ref('')
const activeTab = ref('all')

async function fetchList() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (activeTab.value !== 'all') {
      params.type = activeTab.value
    }
    if (searchKw.value.trim()) {
      params.search = searchKw.value.trim()
    }

    const res = await Axios.get('/favorite_list', { params })
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

function doSearch() {
  page.value = 1
  fetchList()
}

function onTabChange() {
  page.value = 1
  fetchList()
}

async function removeItem(item: FavItem) {
  try {
    await ElMessageBox.confirm(`确定取消收藏「${item.name}」吗？`, '提示', {
      confirmButtonText: '取消收藏',
      cancelButtonText: '保留',
      type: 'warning',
    })
  } catch {
    return
  }

  removingId.value = item.id
  try {
    const res = await Axios.delete('/favorite_remove', { params: { id: item.id } })
    if (res.data.success) {
      ElMessage.success('已取消收藏')
      await fetchList()
    } else {
      ElMessage.error(res.data.msg || '取消失败')
    }
  } catch {
    ElMessage.error('网络异常，请稍后重试')
  } finally {
    removingId.value = null
  }
}

function goDetail(item: FavItem) {
  if (!item.available) return
  if (item.type === 'commodity') {
    router.push(`/commodity/${item.mall_id}/${item.shopping_id}`)
  } else {
    router.push(`/store/${item.mall_id}`)
  }
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
.fav-container {
  width: 100%;
  max-width: 720px;
  padding: 20px 24px;
  box-sizing: border-box;
}

.fav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.fav-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.fav-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.fav-loading {
  padding: 16px 0;
}

.fav-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 8px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.15s;
  border-radius: 6px;
  cursor: pointer;
}

.fav-item:hover {
  background: #fafafa;
}

.fav-item--unavailable {
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
  display: flex;
  align-items: center;
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

.item-desc {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}

.item-time {
  font-size: 12px;
  color: #b0b3bb;
}

.item-delete {
  flex-shrink: 0;
  margin-left: auto;
}

.fav-pagination {
  display: flex;
  justify-content: center;
  padding-top: 20px;
}
</style>
