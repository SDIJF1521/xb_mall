<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <AppNavigation/>
      </el-header>
      <el-main>
        <HeadSearch/>
      </el-main>
      <el-container>
        <el-container>
          <el-main>
            <div v-if="loading && goods.length === 0" class="loading-wrapper">
              <el-skeleton :rows="4" animated />
            </div>
            <template v-else>
              <NullPage v-if="goods.length === 0" />
              <template v-else>
                <MallGoods :goods="goods" />
                <!-- 搜索模式：懒加载，底部加载更多 -->
                <div
                  v-if="isSearchMode"
                  ref="loadMoreRef"
                  class="load-more-sentinel"
                >
                  <div v-if="loading" class="loading-more">
                    <el-icon class="is-loading"><Loading /></el-icon>
                    <span>加载中...</span>
                  </div>
                  <div v-else-if="hasMore" class="load-more-hint">滚动加载更多</div>
                  <div v-else-if="goods.length > 0" class="load-more-end">已加载全部 {{ total }} 件商品</div>
                </div>
                <!-- 推荐模式：分页 -->
                <div v-else class="pagination-wrapper">
                  <el-pagination
                    v-model:current-page="currentPage"
                    v-model:page-size="pageSize"
                    :page-sizes="[25, 50, 100]"
                    :total="total"
                    layout="total, sizes, prev, pager, next, jumper"
                    background
                    @current-change="onPageChange"
                    @size-change="onPageSizeChange"
                  />
                </div>
              </template>
            </template>
          </el-main>
        </el-container>
      </el-container>
      <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { Loading } from '@element-plus/icons-vue'
import AppNavigation from '@/moon/navigation.vue'
import HeadSearch from '@/views/mall/content/head_search.vue'
import NullPage from '@/views/mall/content/nall_page.vue'
import MallGoods from '@/views/mall/content/mall_goods.vue'

defineOptions({ name: 'Mall' })

interface GoodsItem {
  mall_id: string
  shopping_id: string
  name: string
  info: string
  type: string[]
  price: number
  img: string
}

const route = useRoute()
const loading = ref(true)
const goods = ref<GoodsItem[]>([])
const currentPage = ref(1)
const pageSize = ref(50)
const total = ref(0)
const loadMoreRef = ref<HTMLElement | null>(null)

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

const searchKeyword = computed(() => (route.query.keyword as string) || '')
const isSearchMode = computed(() => !!searchKeyword.value.trim())
const hasMore = computed(() => goods.value.length < total.value)

const getHeaders = () => {
  const token = localStorage.getItem('access_token')
  return token ? { 'access-token': token } : {}
}

/** 获取推荐商品列表（无搜索时使用） */
const fetchRecommend = async (page: number) => {
  loading.value = true
  try {
    const res = await Axios.get('/recommend_commodity_list', {
      params: { page, page_size: pageSize.value },
      headers: getHeaders(),
    })
    if (res.data.success) {
      goods.value = res.data.data || []
      total.value = res.data.total ?? 0
    } else {
      goods.value = []
      total.value = 0
    }
  } catch {
    goods.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

/** 搜索商品（支持懒加载追加） */
const fetchSearch = async (page: number, append = false) => {
  const kw = searchKeyword.value.trim()
  if (!kw) return
  loading.value = true
  try {
    const res = await Axios.get('/mall_commodity_search', {
      params: { keyword: kw, page, page_size: pageSize.value },
    })
    if (res.data.success) {
      const newData = res.data.data || []
      if (append) {
        goods.value = [...goods.value, ...newData]
      } else {
        goods.value = newData
      }
      total.value = res.data.total ?? 0
    } else {
      if (!append) {
        goods.value = []
        total.value = 0
      }
    }
  } catch {
    if (!append) {
      goods.value = []
      total.value = 0
    }
  } finally {
    loading.value = false
  }
}

const onPageChange = (page: number) => {
  currentPage.value = page
  window.scrollTo({ top: 0, behavior: 'smooth' })
  fetchRecommend(page)
}

const onPageSizeChange = () => {
  currentPage.value = 1
  fetchRecommend(1)
}

/** 懒加载：滚动到底部时加载下一页 */
let observer: IntersectionObserver | null = null
const setupLoadMoreObserver = () => {
  teardownLoadMoreObserver()
  if (!loadMoreRef.value || !isSearchMode.value || loading.value || !hasMore.value) return
  observer = new IntersectionObserver(
    (entries) => {
      const entry = entries[0]
      if (!entry?.isIntersecting || loading.value || !hasMore.value) return
      currentPage.value += 1
      fetchSearch(currentPage.value, true)
    },
    { rootMargin: '100px', threshold: 0.1 }
  )
  observer.observe(loadMoreRef.value)
}

const teardownLoadMoreObserver = () => {
  if (observer) {
    if (loadMoreRef.value) {
      try {
        observer.unobserve(loadMoreRef.value)
      } catch {
        /* 忽略 */
      }
    }
    observer.disconnect()
    observer = null
  }
}

/** 根据模式加载数据 */
const loadData = () => {
  currentPage.value = 1
  if (isSearchMode.value) {
    fetchSearch(1, false)
  } else {
    fetchRecommend(1)
  }
}

watch(
  () => route.query.keyword,
  () => {
    loadData()
  },
  { immediate: false }
)

/** 搜索模式下载入完成后，设置懒加载观察器 */
watch(
  () => [loading.value, hasMore.value, goods.value.length],
  () => {
    if (!loading.value && isSearchMode.value && hasMore.value) {
      nextTick(() => setupLoadMoreObserver())
    } else {
      teardownLoadMoreObserver()
    }
  }
)

onMounted(() => {
  loadData()
})

onUnmounted(() => {
  teardownLoadMoreObserver()
})
</script>

<style scoped>
.footer-content {
  text-align: center;
  color: darkgray;
}

.loading-wrapper {
  padding: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 32px 0 16px;
}

.load-more-sentinel {
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 0;
}

.loading-more,
.load-more-hint,
.load-more-end {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-size: 14px;
}
</style>
