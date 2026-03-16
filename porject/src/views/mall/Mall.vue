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
            <div v-if="loading" class="loading-wrapper">
              <el-skeleton :rows="4" animated />
            </div>
            <template v-else>
              <NullPage v-if="goods.length === 0" />
              <template v-else>
                <MallGoods :goods="goods" />
                <div class="pagination-wrapper">
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
import { ref, onMounted } from 'vue'
import axios from 'axios'
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

const loading = ref(true)
const goods = ref<GoodsItem[]>([])
const currentPage = ref(1)
const pageSize = ref(50)
const total = ref(0)

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

const getHeaders = () => {
  const token = localStorage.getItem('access_token')
  return token ? { 'access-token': token } : {}
}

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

const onPageChange = (page: number) => {
  currentPage.value = page
  window.scrollTo({ top: 0, behavior: 'smooth' })
  fetchRecommend(page)
}

const onPageSizeChange = () => {
  currentPage.value = 1
  fetchRecommend(1)
}

onMounted(() => fetchRecommend(1))
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
</style>
