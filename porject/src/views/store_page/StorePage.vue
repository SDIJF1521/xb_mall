<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <AppNavigation />
      </el-header>

      <el-main class="store-main">
        <!-- 店铺不存在 -->
        <el-result
          v-if="!storeLoading && storeError"
          icon="error"
          title="店铺不存在"
          :sub-title="storeError"
        >
          <template #extra>
            <el-button type="primary" @click="router.push('/mall')">返回商城</el-button>
          </template>
        </el-result>

        <template v-else>
          <!-- 店铺信息卡 -->
          <StoreInfoCard
            :store="store"
            :loading="storeLoading"
            :is-favorited="isFavorited"
            @favorite="handleFavorite"
            @service="handleService"
          />

          <!-- 商品列表 -->
          <StoreCommodityList
            :list="commodityList"
            :loading="listLoading"
            :store-loading="storeLoading"
            :total="total"
            :page="page"
            :page-size="pageSize"
            :keyword="searchKeyword"
            @update:page="onPageChange"
            @update:page-size="onPageSizeChange"
            @update:keyword="searchKeyword = $event"
            @search="onSearch"
            @clear-search="onClearSearch"
            @go-detail="goDetail"
          />
        </template>
      </el-main>

      <el-footer class="footer-content">版权所有 © [xb商城]，保留所有权利。</el-footer>
    </el-container>

    <!-- 悬浮客服 -->
    <CustomerService
      v-if="!storeLoading && !storeError"
      ref="csRef"
      :mall-id="mallId"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

import AppNavigation from '@/moon/navigation.vue'
import StoreInfoCard from './components/StoreInfoCard.vue'
import StoreCommodityList from './components/StoreCommodityList.vue'
import CustomerService from '@/moon/CustomerService.vue'
import type { StoreInfo } from './components/StoreInfoCard.vue'
import type { CommodityItem } from './components/StoreCommodityList.vue'

const route = useRoute()
const router = useRouter()

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const mallId = Number(route.params.mall_id)

/* ── 客服组件引用 ── */
const csRef = ref<{ openChat: () => void } | null>(null)

/* ── 店铺信息状态 ── */
const store = ref<StoreInfo | null>(null)
const storeLoading = ref(false)
const storeError = ref('')
const isFavorited = ref(false)

/* ── 商品列表状态 ── */
const commodityList = ref<CommodityItem[]>([])
const listLoading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(12)
const searchKeyword = ref('')

/* ── API 调用 ── */
const fetchStore = async () => {
  storeLoading.value = true
  storeError.value = ''
  try {
    const res = await Axios.get('/store_info', { params: { mall_id: mallId } })
    if (res.data.success) {
      store.value = res.data.data
    } else {
      storeError.value = res.data.msg || '店铺不存在'
    }
  } catch {
    storeError.value = '网络异常，请稍后重试'
  } finally {
    storeLoading.value = false
  }
}

const fetchCommodities = async () => {
  listLoading.value = true
  try {
    const res = await Axios.get('/store_commodity_list', {
      params: {
        mall_id: mallId,
        page: page.value,
        page_size: pageSize.value,
        search: searchKeyword.value || undefined,
      },
    })
    if (res.data.success) {
      commodityList.value = res.data.data || []
      total.value = res.data.total ?? 0
    } else {
      commodityList.value = []
      total.value = 0
    }
  } catch {
    ElMessage.error('获取商品列表失败')
    commodityList.value = []
    total.value = 0
  } finally {
    listLoading.value = false
  }
}

/* ── 事件处理 ── */
const onSearch = () => {
  page.value = 1
  fetchCommodities()
}

const onClearSearch = () => {
  searchKeyword.value = ''
  page.value = 1
  fetchCommodities()
}

const onPageChange = (val: number) => {
  page.value = val
  fetchCommodities()
}

const onPageSizeChange = (val: number) => {
  pageSize.value = val
  page.value = 1
  fetchCommodities()
}

const goDetail = (item: CommodityItem) => {
  router.push(`/commodity/${item.mall_id}/${item.shopping_id}`)
}

const favId = ref<number | null>(null)

const getHeaders = () => {
  const token = localStorage.getItem('access_token')
  return token ? { 'access-token': token } : {}
}

const checkFavorite = async () => {
  const token = localStorage.getItem('access_token')
  if (!token) return
  try {
    const res = await Axios.get('/favorite_check', {
      params: { type: 'store', mall_id: mallId },
      headers: getHeaders(),
    })
    if (res.data.success) {
      isFavorited.value = res.data.is_favorited
      favId.value = res.data.favorite_id ?? null
    }
  } catch { /* ignore */ }
}

const handleFavorite = async () => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    ElMessage.warning('请先登录')
    router.push('/register')
    return
  }
  try {
    if (isFavorited.value && favId.value) {
      const res = await Axios.delete('/favorite_remove', {
        params: { id: favId.value },
        headers: getHeaders(),
      })
      if (res.data.success) {
        isFavorited.value = false
        favId.value = null
        ElMessage.success('已取消收藏')
      } else {
        ElMessage.warning(res.data.msg || '操作失败')
      }
    } else {
      const res = await Axios.post(
        '/favorite_add',
        { type: 'store', mall_id: mallId },
        { headers: getHeaders() },
      )
      if (res.data.success) {
        isFavorited.value = true
        await checkFavorite()
        ElMessage.success('已收藏店铺')
      } else {
        ElMessage.warning(res.data.msg || '操作失败')
      }
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  }
}

// 点击"联系客服"按钮，主动打开悬浮客服面板
const handleService = () => {
  csRef.value?.openChat()
}

onMounted(async () => {
  await fetchStore()
  if (store.value) {
    fetchCommodities()
    checkFavorite()
  }
})
</script>

<style scoped lang="scss">
.common-layout {
  min-height: 100vh;
  background: var(--color-background-soft);
}

.store-main {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px 24px 64px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.footer-content {
  text-align: center;
  color: var(--vt-c-text-light-2);
  font-size: 13px;
}

html.dark .footer-content {
  color: var(--vt-c-text-dark-2);
}
</style>
