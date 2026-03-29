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
                  :mall-id="commodity.mall_id"
                  :buy-loading="buyLoading"
                  :cart-loading="cartLoading"
                  :wishlist-loading="wishlistLoading"
                  :is-wishlisted="isWishlisted"
                  @buy="handleBuy"
                  @add-to-cart="handleAddToCart"
                  @wishlist="handleWishlist"
                  @service="csRef?.openChat()"
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

      <el-footer class="footer-content">版权所有 ©[xb商城]，保留所有权利。</el-footer>
    </el-container>

    <!-- 悬浮客服 -->
    <CustomerService
      v-if="commodity"
      ref="csRef"
      :mall-id="commodity.mall_id"
      :shopping-id="commodity.shopping_id"
      :commodity="commodity"
    />

    <!-- 优惠券选择弹窗 -->
    <el-dialog v-model="couponDialogVisible" title="确认订单 - 选择优惠券" width="520px" destroy-on-close>
      <div class="order-summary">
        <p>商品金额：<b>¥{{ pendingOrderAmount.toFixed(2) }}</b></p>
      </div>
      <div v-if="usableCoupons.length > 0" class="coupon-select-list">
        <div v-for="c in usableCoupons" :key="c.user_coupon_id"
             class="coupon-select-item"
             :class="{ active: selectedCouponId === c.user_coupon_id }"
             @click="selectedCouponId = selectedCouponId === c.user_coupon_id ? null : c.user_coupon_id">
          <div class="cs-left" :class="`cs-bg-${c.coupon_type}`">
            <template v-if="c.coupon_type === 'discount'">
              <span class="cs-amount">{{ c.discount_value }}</span><span class="cs-unit">折</span>
            </template>
            <template v-else>
              <span class="cs-unit">¥</span><span class="cs-amount">{{ c.discount_value }}</span>
            </template>
          </div>
          <div class="cs-right">
            <div class="cs-name">{{ c.name }}</div>
            <div class="cs-desc">满{{ c.min_order_amount }}元可用 · 预计优惠 ¥{{ c.estimated_discount.toFixed(2) }}</div>
          </div>
          <el-icon v-if="selectedCouponId === c.user_coupon_id" class="cs-check"><Select /></el-icon>
        </div>
      </div>
      <el-empty v-else description="暂无可用优惠券" :image-size="60" />
      <div class="order-pay-summary" v-if="selectedCoupon">
        <span>优惠：-¥{{ selectedCoupon.estimated_discount.toFixed(2) }}</span>
        <span class="pay-total">实付：¥{{ (pendingOrderAmount - selectedCoupon.estimated_discount).toFixed(2) }}</span>
      </div>
      <template #footer>
        <el-button @click="couponDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="buyLoading" @click="confirmOrder">
          {{ selectedCouponId ? '使用优惠券下单' : '不使用优惠券下单' }}
        </el-button>
      </template>
    </el-dialog>
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
import CustomerService from '@/moon/CustomerService.vue'

interface Spec {
  specs: string[]
  price: number
  stock: number
  specification_id?: number
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

/* ── 客服组件引用 ── */
const csRef = ref<{ openChat: () => void } | null>(null)

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
  const token = localStorage.getItem('access_token')
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

/* ── 优惠券相关 ── */
const couponDialogVisible = ref(false)
const usableCoupons = ref<any[]>([])
const selectedCouponId = ref<number | null>(null)
const pendingOrderAmount = ref(0)
const pendingBuyParams = ref<{ specIndex: number; quantity: number; addressId: number } | null>(null)

const selectedCoupon = computed(() => {
  if (!selectedCouponId.value) return null
  return usableCoupons.value.find((c: any) => c.user_coupon_id === selectedCouponId.value) || null
})

const handleBuy = async ({ specIndex, quantity }: { specIndex: number; quantity: number }) => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    ElMessage.warning('请先登录')
    router.push('/register')
    return
  }
  if (!commodity.value) return

  buyLoading.value = true
  try {
    const addrRes = await Axios.post('/get_address_apply', new URLSearchParams({ token }))
    if (!addrRes.data?.current || !addrRes.data?.data) {
      ElMessage.warning('请先设置收货地址')
      router.push('/addre_set')
      return
    }

    const listRes = await Axios.post('/get_address', new URLSearchParams({ token }))
    if (!listRes.data?.current) {
      ElMessage.warning('获取地址失败，请重试')
      return
    }
    const addrList = listRes.data.save_list
    let defaultAddrId: number | null = null
    for (const key of Object.keys(addrList)) {
      const row = addrList[key]
      if (row[8] === 1) {
        defaultAddrId = row[1]
        break
      }
    }
    if (!defaultAddrId) {
      ElMessage.warning('请先设置默认收货地址')
      router.push('/addre_set')
      return
    }

    const specList = commodity.value.specification_list || []
    const spec = specList[specIndex]
    const price = spec?.price ?? 0
    const orderAmount = +(price * quantity).toFixed(2)

    pendingOrderAmount.value = orderAmount
    pendingBuyParams.value = { specIndex, quantity, addressId: defaultAddrId }
    selectedCouponId.value = null

    try {
      const couponRes = await Axios.get('/user_coupon/usable', {
        params: { mall_id: commodity.value.mall_id, order_amount: orderAmount },
        headers: getHeaders(),
      })
      usableCoupons.value = couponRes.data?.list || []
    } catch {
      usableCoupons.value = []
    }

    couponDialogVisible.value = true
  } catch (err: unknown) {
    const status = (err as { response?: { status?: number } })?.response?.status
    if (status === 401 || status === 403) {
      ElMessage.warning('请先登录')
      router.push('/register')
    } else {
      ElMessage.error('准备下单失败，请稍后重试')
    }
  } finally {
    buyLoading.value = false
  }
}

const confirmOrder = async () => {
  if (!commodity.value || !pendingBuyParams.value) return

  buyLoading.value = true
  try {
    const { specIndex, quantity, addressId } = pendingBuyParams.value
    const specList = commodity.value.specification_list || []
    const spec = specList[specIndex]
    const specificationId = spec?.specification_id ?? specIndex

    const idempotencyKey = `buy_${commodity.value.mall_id}_${commodity.value.shopping_id}_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
    const body: any = {
      items: [{
        mall_id: commodity.value.mall_id,
        shopping_id: commodity.value.shopping_id,
        specification_id: specificationId,
        quantity,
      }],
      address_id: addressId,
      idempotency_key: idempotencyKey,
    }
    if (selectedCouponId.value) {
      body.user_coupon_id = selectedCouponId.value
    }

    const orderRes = await Axios.post('/order/create', body, { headers: getHeaders() })

    if (orderRes.data?.success) {
      couponDialogVisible.value = false
      const discount = orderRes.data.coupon_discount
      const msg = discount ? `下单成功，优惠 ¥${discount.toFixed(2)}，请在15分钟内完成支付` : '下单成功，请在15分钟内完成支付'
      ElMessage.success(msg)
      router.push('/personal_center?tab=orders')
    } else {
      ElMessage.error(orderRes.data?.msg || '下单失败')
    }
  } catch (err: unknown) {
    const status = (err as { response?: { status?: number } })?.response?.status
    if (status === 401 || status === 403) {
      ElMessage.warning('请先登录')
      router.push('/register')
    } else {
      ElMessage.error('下单失败，请稍后重试')
    }
  } finally {
    buyLoading.value = false
  }
}

const handleAddToCart = async ({ specIndex, quantity }: { specIndex: number; quantity: number }) => {
  const token = localStorage.getItem('access_token')
  if (!token) {
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
  } catch (err: unknown) {
    const status = (err as { response?: { status?: number } })?.response?.status
    if (status === 401 || status === 403) {
      ElMessage.warning('请先登录')
      router.push('/register')
    } else {
      ElMessage.error('加入购物车失败')
    }
  } finally {
    cartLoading.value = false
  }
}

const favId = ref<number | null>(null)

const checkFavorite = async () => {
  const token = localStorage.getItem('access_token')
  if (!token || !commodity.value) return
  try {
    const res = await Axios.get('/favorite_check', {
      params: {
        type: 'commodity',
        mall_id: commodity.value.mall_id,
        shopping_id: commodity.value.shopping_id,
      },
      headers: getHeaders(),
    })
    if (res.data.success) {
      isWishlisted.value = res.data.is_favorited
      favId.value = res.data.favorite_id ?? null
    }
  } catch { /* ignore */ }
}

const handleWishlist = async () => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    ElMessage.warning('请先登录')
    router.push('/register')
    return
  }
  wishlistLoading.value = true
  try {
    if (isWishlisted.value && favId.value) {
      const res = await Axios.delete('/favorite_remove', {
        params: { id: favId.value },
        headers: getHeaders(),
      })
      if (res.data.success) {
        isWishlisted.value = false
        favId.value = null
        ElMessage.success('已取消收藏')
      } else {
        ElMessage.warning(res.data.msg || '操作失败')
      }
    } else {
      const res = await Axios.post(
        '/favorite_add',
        {
          type: 'commodity',
          mall_id: commodity.value?.mall_id,
          shopping_id: commodity.value?.shopping_id,
        },
        { headers: getHeaders() },
      )
      if (res.data.success) {
        isWishlisted.value = true
        await checkFavorite()
        ElMessage.success('已加入收藏')
      } else {
        ElMessage.warning(res.data.msg || '操作失败')
      }
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    wishlistLoading.value = false
  }
}

onMounted(async () => {
  await fetchCommodity()
  await checkFavorite()
})
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

/* 优惠券选择弹窗 */
.order-summary {
  margin-bottom: 12px;
  font-size: 14px;
}
.coupon-select-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}
.coupon-select-item {
  display: flex;
  align-items: center;
  border: 2px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.2s;
  overflow: hidden;
}
.coupon-select-item.active {
  border-color: #409eff;
}
.coupon-select-item:hover {
  border-color: #b3d8ff;
}
.cs-left {
  width: 80px;
  display: flex;
  justify-content: center;
  align-items: baseline;
  padding: 12px 8px;
  color: #fff;
  flex-shrink: 0;
}
.cs-bg-full_reduction { background: linear-gradient(135deg, #ff6b6b, #ee5a24); }
.cs-bg-discount { background: linear-gradient(135deg, #4834d4, #6c5ce7); }
.cs-bg-fixed_amount { background: linear-gradient(135deg, #f0932b, #ffbe76); }
.cs-amount { font-size: 22px; font-weight: bold; }
.cs-unit { font-size: 12px; }
.cs-right {
  flex: 1;
  padding: 8px 12px;
}
.cs-name { font-size: 14px; font-weight: 500; }
.cs-desc { font-size: 12px; color: #999; margin-top: 2px; }
.cs-check {
  margin-right: 12px;
  color: #409eff;
  font-size: 20px;
}
.order-pay-summary {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  margin-top: 12px;
  font-size: 14px;
}
.pay-total {
  color: #f56c6c;
  font-weight: bold;
  font-size: 16px;
}
</style>
