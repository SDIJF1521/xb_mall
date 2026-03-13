<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <AppNavigation />
      </el-header>

      <el-main class="page-main">
        <!-- 加载骨架屏 -->
        <div v-if="loading" class="skeleton-wrap">
          <el-skeleton animated>
            <template #template>
              <div class="skeleton-layout">
                <el-skeleton-item variant="image" style="width:460px;height:460px;border-radius:16px" />
                <div class="skeleton-right">
                  <el-skeleton-item variant="h1" style="width:70%;height:32px" />
                  <el-skeleton-item variant="text" style="width:40%;height:24px;margin-top:16px" />
                  <el-skeleton-item variant="text" style="width:100%;height:16px;margin-top:24px" />
                  <el-skeleton-item variant="text" style="width:80%;height:16px;margin-top:8px" />
                  <el-skeleton-item variant="button" style="width:100%;height:52px;margin-top:32px;border-radius:26px" />
                </div>
              </div>
            </template>
          </el-skeleton>
        </div>

        <!-- 错误状态 -->
        <div v-else-if="error" class="error-wrap">
          <el-result icon="error" title="加载失败" :sub-title="error">
            <template #extra>
              <el-button type="primary" @click="fetchCommodity">重新加载</el-button>
              <el-button @click="router.back()">返回上一页</el-button>
            </template>
          </el-result>
        </div>

        <!-- 商品详情内容 -->
        <template v-else-if="commodity">
          <!-- 面包屑导航 -->
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-for="t in commodity.type" :key="t">{{ t }}</el-breadcrumb-item>
            <el-breadcrumb-item>{{ commodity.name }}</el-breadcrumb-item>
          </el-breadcrumb>

          <!-- 上半区：图片 + 购买 -->
          <div class="top-section">
            <div class="gallery-col">
              <CommodityGallery :img-list="imgList" />
            </div>
            <div class="purchase-col">
              <el-card shadow="never" class="purchase-card">
                <CommodityPurchase
                  :commodity="commodity"
                  :buy-loading="buyLoading"
                  :cart-loading="cartLoading"
                  :wishlist-loading="wishlistLoading"
                  :is-wishlisted="isWishlisted"
                  @buy="handleBuy"
                  @add-to-cart="handleAddToCart"
                  @wishlist="handleWishlist"
                />
              </el-card>
            </div>
          </div>

          <!-- 下半区：简介 + 评论 -->
          <div class="bottom-section">
            <CommodityDescription
              :info="commodity.info"
              :spec-list="commodity.specification_list"
            />
            <CommentSection
              :shopping-id="commodity.shopping_id"
              :mall-id="commodity.mall_id"
            />
          </div>
        </template>
      </el-main>

      <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
    </el-container>

    <!-- 悬浮客服 -->
    <CustomerService
      v-if="commodity"
      :mall-id="commodity.mall_id"
      :shopping-id="commodity.shopping_id"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

import AppNavigation from '@/moon/navigation.vue'
import CommodityGallery from './components/CommodityGallery.vue'
import CommodityPurchase from './components/CommodityPurchase.vue'
import CommodityDescription from './components/CommodityDescription.vue'
import CommentSection from './components/CommentSection.vue'
import CustomerService from './components/CustomerService.vue'

interface Spec {
  specs: string[]
  price: number
  stock: number
}

interface Commodity {
  shopping_id: number
  mall_id: number
  name: string
  info: string
  type: string[]
  price: number
  img_list: string[]
  specification_list: Spec[]
}

const route = useRoute()
const router = useRouter()

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

const loading = ref(false)
const error = ref('')
const commodity = ref<Commodity | null>(null)
const isWishlisted = ref(false)
const buyLoading = ref(false)
const cartLoading = ref(false)
const wishlistLoading = ref(false)

const imgList = computed(() => {
  if (!commodity.value?.img_list?.length) return []
  return commodity.value.img_list.map((img) =>
    img.startsWith('data:') ? img : `data:image/jpeg;base64,${img}`
  )
})

const getHeaders = () => {
  const token = localStorage.getItem('buyer_access_token')
  return token ? { 'access-token': token } : {}
}

const fetchCommodity = async () => {
  const { mall_id, shopping_id } = route.params
  error.value = ''
  loading.value = true
  try {
    const res = await Axios.get('/commodity_detail', {
      params: { mall_id, shopping_id },
      headers: getHeaders(),
    })
    if (res.data.success) {
      commodity.value = res.data.data
    } else {
      error.value = res.data.msg || '商品不存在'
    }
  } catch {
    error.value = '网络异常，请检查连接后重试'
  } finally {
    loading.value = false
  }
}

const handleBuy = async ({ specIndex, quantity }: { specIndex: number; quantity: number }) => {
  if (!localStorage.getItem('buyer_access_token')) {
    ElMessage.warning('请先登录')
    router.push('/register')
    return
  }
  buyLoading.value = true
  try {
    // 对接立即购买接口
    ElMessage.success('跳转结算中...')
  } finally {
    buyLoading.value = false
  }
}

const handleAddToCart = async ({ specIndex, quantity }: { specIndex: number; quantity: number }) => {
  if (!localStorage.getItem('buyer_access_token')) {
    ElMessage.warning('请先登录')
    router.push('/register')
    return
  }
  cartLoading.value = true
  try {
    const res = await Axios.post(
      '/shopping_cart_add',
      {
        shopping_id: commodity.value?.shopping_id,
        mall_id: commodity.value?.mall_id,
        spec_index: specIndex,
        quantity,
      },
      { headers: getHeaders() }
    )
    if (res.data.success) {
      ElMessage.success('已加入购物车')
    } else {
      ElMessage.warning(res.data.msg || '操作失败')
    }
  } catch {
    ElMessage.error('加入购物车失败')
  } finally {
    cartLoading.value = false
  }
}

const handleWishlist = async () => {
  if (!localStorage.getItem('buyer_access_token')) {
    ElMessage.warning('请先登录')
    return
  }
  wishlistLoading.value = true
  try {
    isWishlisted.value = !isWishlisted.value
    ElMessage.success(isWishlisted.value ? '已加入收藏' : '已取消收藏')
  } finally {
    wishlistLoading.value = false
  }
}

onMounted(fetchCommodity)
</script>

<style scoped lang="scss">
.common-layout {
  min-height: 100vh;
  background: var(--color-background-soft);
}

/* ── 面包屑 ── */
.breadcrumb {
  font-size: 13px;
  padding: 4px 0;
}

/* ── 骨架屏 ── */
.skeleton-wrap {
  .skeleton-layout {
    display: flex;
    gap: 40px;
    .skeleton-right {
      flex: 1;
      display: flex;
      flex-direction: column;
    }
  }
}

/* ── 错误页 ── */
.error-wrap { padding: 60px 0; }

/* ── 主内容区 ── */
.page-main {
  max-width: 1280px;
  margin: 0 auto;
  padding: 20px 24px 64px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 上半区：图片 + 购买面板 */
.top-section {
  display: grid;
  grid-template-columns: 460px 1fr;
  gap: 28px;
  align-items: flex-start;

  @media (max-width: 960px) { grid-template-columns: 1fr; }
}

.gallery-col {
  position: sticky;
  top: 16px;
}

.purchase-col {
  .purchase-card {
    border-radius: 20px;
    border: 1px solid var(--color-border);
    background: var(--el-bg-color);
    box-shadow: 0 2px 16px rgba(0,0,0,0.04);

    :deep(.el-card__body) { padding: 28px; }
  }
}

/* 下半区 */
.bottom-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.footer-content {
  text-align: center;
  color: var(--el-text-color-placeholder);
  font-size: 13px;
}
</style>
