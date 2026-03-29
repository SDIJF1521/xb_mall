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

          <!-- 活动横幅：展示所有当前生效活动 -->
          <template v-if="commodity.activities?.length">
            <!-- 多活动叠加提示 -->
            <div v-if="commodity.activities.length > 1" class="activity-stack-tip">
              <el-icon style="vertical-align: middle; margin-right: 4px"><Lightning /></el-icon>
              当前共 <b>{{ commodity.activities.length }}</b> 个活动叠加生效，已为您自动计算最优价格
            </div>

            <!-- 每个活动一条横幅 -->
            <div
              v-for="(act, idx) in commodity.activities"
              :key="idx"
              class="activity-strip"
              :class="`activity-strip--${act.activity_type}`"
            >
              <div class="activity-strip__left">
                <span class="activity-strip__issuer">{{ act.issuer_type === 'platform' ? '平台' : '商家' }}</span>
                <span class="activity-strip__badge">{{ activityTypeLabel(act.activity_type) }}</span>
                <span class="activity-strip__name">{{ act.activity_name }}</span>
                <span v-if="activityDiscountText(act)" class="activity-strip__discount">{{ activityDiscountText(act) }}</span>
              </div>
              <div v-if="idx === 0" class="activity-strip__right">
                <span class="activity-strip__countdown-label">距结束</span>
                <span class="activity-strip__countdown">{{ countdownStr }}</span>
              </div>
            </div>
          </template>

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

    <!-- 优惠券 / 优惠方式选择弹窗 -->
    <el-dialog
      v-model="couponDialogVisible"
      :title="isNonStackable ? '确认订单 - 选择优惠方式' : '确认订单 - 选择优惠券'"
      width="520px"
      destroy-on-close
    >
      <!-- ① 不可叠加：让用户在"活动折扣"和"优惠券"中二选一 -->
      <template v-if="isNonStackable">
        <el-alert
          title="当前活动不支持叠加优惠券，请选择一种优惠方式"
          type="warning" :closable="false" show-icon style="margin-bottom: 14px"
        />
        <el-radio-group v-model="discountPreference" style="margin-bottom: 14px; display: flex; gap: 12px">
          <el-radio-button value="activity">
            使用活动折扣（¥{{ pendingOrderAmount.toFixed(2) }}）
          </el-radio-button>
          <el-radio-button value="coupon">
            使用优惠券（原价 ¥{{ originalOrderAmount.toFixed(2) }}）
          </el-radio-button>
        </el-radio-group>

        <!-- 活动折扣模式：无需选券 -->
        <div v-if="discountPreference === 'activity'" class="order-summary">
          <p>活动折后价：<b style="color:#cf1322">¥{{ pendingOrderAmount.toFixed(2) }}</b></p>
          <p style="font-size:12px;color:var(--el-text-color-secondary)">
            不可叠加优惠券，活动优惠已自动计算
          </p>
        </div>

        <!-- 优惠券模式：以原价匹配可用券 -->
        <div v-else>
          <div class="order-summary">
            <p>以原价计算：<b>¥{{ originalOrderAmount.toFixed(2) }}</b>（活动折扣不生效）</p>
          </div>
          <div v-if="usableCouponsForOriginal.length > 0" class="coupon-select-list">
            <div
              v-for="c in usableCouponsForOriginal"
              :key="c.user_coupon_id"
              class="coupon-select-item"
              :class="{ active: selectedCouponId === c.user_coupon_id }"
              @click="selectedCouponId = selectedCouponId === c.user_coupon_id ? null : c.user_coupon_id"
            >
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
        </div>
      </template>

      <!-- ② 可叠加（或无折扣活动）：正常选券叠加 -->
      <template v-else>
        <div class="order-summary">
          <p>
            活动折后金额：<b>¥{{ pendingOrderAmount.toFixed(2) }}</b>
            <el-tag v-if="isStackable" size="small" type="success" style="margin-left: 6px">支持折上折</el-tag>
          </p>
          <p v-if="isStackable" style="font-size:12px;color:var(--el-color-success)">
            选择优惠券可在活动价基础上进一步叠加优惠
          </p>
        </div>
        <div v-if="usableCoupons.length > 0" class="coupon-select-list">
          <div
            v-for="c in usableCoupons"
            :key="c.user_coupon_id"
            class="coupon-select-item"
            :class="{ active: selectedCouponId === c.user_coupon_id }"
            @click="selectedCouponId = selectedCouponId === c.user_coupon_id ? null : c.user_coupon_id"
          >
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
      </template>

      <!-- 实付汇总 -->
      <div class="order-pay-summary">
        <template v-if="isNonStackable && discountPreference === 'activity'">
          <span>活动优惠：-¥{{ (originalOrderAmount - pendingOrderAmount).toFixed(2) }}</span>
          <span class="pay-total">实付：¥{{ pendingOrderAmount.toFixed(2) }}</span>
        </template>
        <template v-else-if="selectedCoupon">
          <template v-if="isNonStackable && discountPreference === 'coupon'">
            <span>优惠券优惠：-¥{{ selectedCoupon.estimated_discount.toFixed(2) }}</span>
            <span class="pay-total">实付：¥{{ Math.max(originalOrderAmount - selectedCoupon.estimated_discount, 0.01).toFixed(2) }}</span>
          </template>
          <template v-else>
            <span>活动 + 优惠券叠加：-¥{{ (originalOrderAmount - pendingOrderAmount + selectedCoupon.estimated_discount).toFixed(2) }}</span>
            <span class="pay-total">实付：¥{{ Math.max(pendingOrderAmount - selectedCoupon.estimated_discount, 0.01).toFixed(2) }}</span>
          </template>
        </template>
        <template v-else>
          <span style="color:var(--el-text-color-placeholder)">未选择优惠券</span>
          <span class="pay-total">实付：¥{{ pendingOrderAmount.toFixed(2) }}</span>
        </template>
      </div>

      <template #footer>
        <el-button @click="couponDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="buyLoading" @click="confirmOrder">
          {{ confirmBtnLabel }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

import { Lightning } from '@element-plus/icons-vue'
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
  original_price?: number | null
  activity_name?: string
  activity_type?: string
}

interface ActivityInfo {
  activity_name: string
  activity_type: string
  discount_rate?: number | null
  end_time?: string
  rules?: Record<string, any>
  issuer_type?: string
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
  activities?: ActivityInfo[]
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
const usableCoupons = ref<any[]>([])          // 基于活动价查出的可用券
const usableCouponsForOriginal = ref<any[]>([]) // 基于原价查出的可用券（不可叠加/券模式用）
const selectedCouponId = ref<number | null>(null)
const pendingOrderAmount = ref(0)             // 活动折后金额
const pendingOriginalAmount = ref(0)          // 商品原价金额（用于不可叠加时券模式）
const pendingBuyParams = ref<{ specIndex: number; quantity: number; addressId: number } | null>(null)

/** 当前选中的券（从 usableCoupons 或 usableCouponsForOriginal 中查找） */
const selectedCoupon = computed(() => {
  if (!selectedCouponId.value) return null
  const all = [...usableCoupons.value, ...usableCouponsForOriginal.value]
  return all.find((c: any) => c.user_coupon_id === selectedCouponId.value) || null
})

/** 是否存在不可叠加活动（明确设置 stackable=false）*/
const isNonStackable = computed(() =>
  commodity.value?.activities?.some(
    (a: any) => a.rules?.stackable === false,
  ) ?? false,
)
/** 是否存在可叠加活动（有活动且未明确禁止叠加，即 stackable !== false）*/
const isStackable = computed(() => {
  const acts = commodity.value?.activities
  if (!acts?.length) return false
  // 只要有任意一个活动没有明确禁止叠加，即视为支持折上折
  return acts.some((a: any) => a.rules?.stackable !== false)
})

/** 不可叠加时用户选择的优惠模式 */
const discountPreference = ref<'activity' | 'coupon'>('activity')

/** 原价金额（无活动时与 pendingOrderAmount 相同） */
const originalOrderAmount = computed(() =>
  pendingOriginalAmount.value || pendingOrderAmount.value,
)

/** 确认按钮文字 */
const confirmBtnLabel = computed(() => {
  if (isNonStackable.value) {
    if (discountPreference.value === 'activity') return '使用活动折扣下单'
    return selectedCouponId.value ? '使用优惠券下单' : '不使用优惠券（原价）下单'
  }
  return selectedCouponId.value ? '使用优惠券下单（折上折）' : '不使用优惠券下单'
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
    const activityPrice = spec?.price ?? 0
    const originalPrice = spec?.original_price ?? activityPrice
    const orderAmount = +(activityPrice * quantity).toFixed(2)
    const origAmount = +(originalPrice * quantity).toFixed(2)

    pendingOrderAmount.value = orderAmount
    pendingOriginalAmount.value = origAmount
    pendingBuyParams.value = { specIndex, quantity, addressId: defaultAddrId }
    selectedCouponId.value = null
    discountPreference.value = 'activity'

    // 拉取两份可用券：活动价基础 + 原价基础（供不可叠加时的券模式使用）
    // 传入 shopping_ids 使后端对商品券进行精确范围验证
    try {
      const [actRes, origRes] = await Promise.all([
        Axios.get('/user_coupon/usable', {
          params: {
            mall_id: commodity.value.mall_id,
            order_amount: orderAmount,
            shopping_ids: commodity.value.shopping_id,
          },
          headers: getHeaders(),
        }),
        origAmount !== orderAmount
          ? Axios.get('/user_coupon/usable', {
              params: {
                mall_id: commodity.value.mall_id,
                order_amount: origAmount,
                shopping_ids: commodity.value.shopping_id,
              },
              headers: getHeaders(),
            })
          : Promise.resolve({ data: { list: [] } }),
      ])
      usableCoupons.value = actRes.data?.list || []
      usableCouponsForOriginal.value = origRes.data?.list || []
    } catch {
      usableCoupons.value = []
      usableCouponsForOriginal.value = []
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
    // 确定优惠模式
    const preferMode = (isNonStackable.value && discountPreference.value === 'coupon')
      ? 'coupon'
      : 'activity'

    const body: any = {
      items: [{
        mall_id: commodity.value.mall_id,
        shopping_id: commodity.value.shopping_id,
        specification_id: specificationId,
        quantity,
      }],
      address_id: addressId,
      idempotency_key: idempotencyKey,
      prefer_mode: preferMode,
    }
    // 仅在「coupon 模式」或「可叠加模式下选了券」时传 user_coupon_id
    if (selectedCouponId.value && (preferMode === 'coupon' || !isNonStackable.value)) {
      body.user_coupon_id = selectedCouponId.value
    }

    const orderRes = await Axios.post('/order/create', body, { headers: getHeaders() })

    if (orderRes.data?.success) {
      couponDialogVisible.value = false
      const totalDiscount = orderRes.data.total_discount
      const actDiscount = orderRes.data.activity_discount
      const couponDiscount = orderRes.data.coupon_discount
      let msg = '下单成功，请在15分钟内完成支付'
      if (totalDiscount > 0) {
        const parts: string[] = []
        if (actDiscount > 0) parts.push(`活动省¥${actDiscount.toFixed(2)}`)
        if (couponDiscount > 0) parts.push(`券省¥${couponDiscount.toFixed(2)}`)
        msg = `下单成功，共节省¥${totalDiscount.toFixed(2)}（${parts.join(' + ')}），请在15分钟内完成支付`
      }
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

// ── 活动倒计时 ──
const countdownStr = ref('')
let countdownTimer: ReturnType<typeof setInterval> | null = null

function startCountdown(endTime: string) {
  if (countdownTimer) clearInterval(countdownTimer)
  function update() {
    const diff = new Date(endTime).getTime() - Date.now()
    if (diff <= 0) {
      countdownStr.value = '已结束'
      if (countdownTimer) clearInterval(countdownTimer)
      return
    }
    const h = Math.floor(diff / 3600000)
    const m = Math.floor((diff % 3600000) / 60000)
    const s = Math.floor((diff % 60000) / 1000)
    countdownStr.value = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }
  update()
  countdownTimer = setInterval(update, 1000)
}

// 工具函数：单个活动的类型标签
function activityTypeLabel(type: string) {
  const map: Record<string, string> = {
    flash_sale: '限时秒杀', full_reduction: '限时满减',
    discount: '限时折扣', group_buy: '拼团优惠',
  }
  return map[type] || '活动'
}

// 工具函数：单个活动的折扣说明文字
function activityDiscountText(act: ActivityInfo) {
  const dr = act.discount_rate
  const rules = act.rules || {}
  if (act.activity_type === 'full_reduction' && rules.thresholds?.length) {
    return rules.thresholds.map((t: any) => `满¥${t.min_amount}减¥${t.reduction}`).join(' / ')
  }
  if (dr != null) return `${(dr * 10).toFixed(1)} 折`
  return ''
}

// 主活动（结束时间最早的，用于倒计时横幅）
const primaryActivity = computed(() => commodity.value?.activities?.[0] ?? null)

onMounted(async () => {
  await fetchCommodity()
  await checkFavorite()
  const endTime = primaryActivity.value?.end_time
  if (endTime) startCountdown(endTime)
})

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
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

/* ── 多活动叠加提示 ── */
.activity-stack-tip {
  padding: 8px 16px;
  background: linear-gradient(135deg, #fffbe6, #fff);
  border: 1.5px solid #ffe58f;
  border-radius: 10px;
  font-size: 13px;
  color: #ad6800;
  font-weight: 500;
}

/* ── 活动横幅 ── */
.activity-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-radius: 12px;
  gap: 12px;
  flex-wrap: wrap;

  &--flash_sale   { background: linear-gradient(135deg, #ff4d4f 0%, #ff7a45 100%); }
  &--discount     { background: linear-gradient(135deg, #722ed1 0%, #9254de 100%); }
  &--group_buy    { background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%); }
  &--full_reduction { background: linear-gradient(135deg, #d4380d 0%, #fa8c16 100%); }

  &__left {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  &__issuer {
    background: rgba(0,0,0,0.2);
    color: rgba(255,255,255,0.9);
    font-size: 11px;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 20px;
    white-space: nowrap;
  }

  &__badge {
    background: rgba(255,255,255,0.25);
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.4);
    white-space: nowrap;
    letter-spacing: 0.5px;
  }

  &__name {
    color: #fff;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.3px;
  }

  &__discount {
    background: rgba(255,255,255,0.18);
    color: #fff;
    font-size: 14px;
    font-weight: 800;
    padding: 2px 12px;
    border-radius: 20px;
    letter-spacing: 0.5px;
  }

  &__right {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  &__countdown-label {
    color: rgba(255,255,255,0.8);
    font-size: 12px;
    white-space: nowrap;
  }

  &__countdown {
    background: rgba(0,0,0,0.25);
    color: #fff;
    font-size: 18px;
    font-weight: 800;
    padding: 4px 14px;
    border-radius: 8px;
    letter-spacing: 3px;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
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
