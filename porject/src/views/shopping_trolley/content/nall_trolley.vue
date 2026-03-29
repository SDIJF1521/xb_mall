<template>
  <div class="cart-container">
    <!-- 顶部栏 -->
    <div class="cart-header">
      <span class="cart-title">购物车</span>
      <div v-if="hasToken && total > 0" class="cart-header-right">
        <span class="cart-count">共 {{ total }} 件</span>
        <el-button
          type="danger"
          size="small"
          plain
          round
          :loading="clearing"
          @click="clearAll"
        >
          全部删除
        </el-button>
      </div>
    </div>

    <!-- 未登录 -->
    <el-empty v-if="!hasToken" description="请先登录查看购物车" :image-size="120">
      <template #extra>
        <router-link to="/register" class="router-button">
          <el-button type="primary" size="large">去登录</el-button>
        </router-link>
      </template>
    </el-empty>

    <!-- 加载中 -->
    <div v-else-if="loading" class="cart-loading">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 空购物车 -->
    <el-empty
      v-else-if="total === 0"
      :description="searchKeyword ? '未找到匹配的商品' : '购物车空空如也'"
      :image-size="120"
    >
      <template #extra>
        <span v-if="searchKeyword" class="empty-hint">试试其他关键词</span>
        <router-link v-else to="/mall" class="router-button">
          <el-button type="primary" size="large">去逛逛</el-button>
        </router-link>
      </template>
    </el-empty>

    <!-- 购物车列表 -->
    <div v-else class="cart-list">
      <div class="cart-select-bar">
        <el-checkbox
          :model-value="allCheckedOnPage"
          :indeterminate="indeterminateOnPage"
          @change="toggleAllOnPage"
        >
          本页全选
        </el-checkbox>
        <span class="select-tip">已勾选 {{ selectedCount }} 件商品</span>
      </div>

      <div
        v-for="(item, index) in list"
        :key="item.id"
        class="cart-item"
        :class="{ 'cart-item--unavailable': !item.available }"
        :style="{ animationDelay: `${index * 0.06}s` }"
      >
        <div class="item-checkbox" @click.stop>
          <el-checkbox
            :model-value="isItemSelected(item.id)"
            :disabled="!item.available"
            @change="(checked: boolean) => toggleItemSelected(item, checked)"
          />
        </div>

        <!-- 商品图片 -->
        <div class="item-img" @click="goDetail(item)">
          <el-image
            v-if="item.img"
            :src="item.img.startsWith('data:') ? item.img : 'data:image/jpeg;base64,' + item.img"
            fit="cover"
            class="img"
          />
          <div v-else class="img img--placeholder">
            <el-icon size="28" class="placeholder-icon"><Picture /></el-icon>
          </div>
          <div v-if="!item.available" class="item-img__mask">已下架</div>
        </div>

        <!-- 商品信息 -->
        <div class="item-info" @click="goDetail(item)">
          <div class="item-name">{{ item.name }}</div>
          <div v-if="item.spec_text" class="item-spec">{{ item.spec_text }}</div>
          <div class="item-meta">
            <span class="item-price">¥ {{ item.price.toFixed(2) }}</span>
            <div class="item-qty-wrap" @click.stop>
              <el-input-number
                :model-value="item.quantity"
                :min="1"
                :max="item.stock"
                :disabled="!item.available || updatingId === item.id"
                size="small"
                controls-position="right"
                class="qty-input"
                @change="(val: number | undefined) => handleQtyChange(item, val)"
              />
            </div>
          </div>
          <div v-if="!item.available" class="item-tip">商品已下架</div>
        </div>

        <!-- 小计 -->
        <div class="item-subtotal">
          ¥ {{ (item.price * item.quantity).toFixed(2) }}
        </div>

        <!-- 删除按钮 -->
        <el-button
          class="item-delete"
          type="danger"
          link
          size="small"
          :loading="deletingId === item.id"
          @click.stop="deleteItem(item)"
        >
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </div>

      <!-- 分页 -->
      <div v-if="total > 0" class="cart-pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[5, 10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @current-change="fetchList"
          @size-change="onPageSizeChange"
        />
      </div>

      <!-- 底部合计 -->
      <div class="cart-footer">
        <div class="cart-total">
          共 {{ total }} 件商品，已勾选 {{ selectedCount }} 件，
          <span class="total-price">勾选合计：¥ {{ selectedTotalPrice.toFixed(2) }}</span>
        </div>
        <div class="cart-footer-btns">
          <el-button type="primary" size="large" class="btn-settle" :loading="settling" @click="handleSettle">
            结算
          </el-button>
          <el-button type="primary" size="large" class="btn-continue" @click="goMall">
            <el-icon><ShoppingCart /></el-icon>
            继续购物
          </el-button>
        </div>
      </div>
    </div>

    <!-- 优惠券选择弹窗 -->
    <el-dialog v-model="couponDialogVisible" title="确认订单 - 选择优惠券" width="520px" destroy-on-close>
      <div class="order-summary">
        <p>商品金额：<b>¥{{ cartPendingAmount.toFixed(2) }}</b></p>
        <el-alert
          title="若商品参与活动（秒杀/满减/拼团/折扣），活动折扣将由系统自动计算；在此基础上可再叠加优惠券（折上折）"
          type="success"
          :closable="false"
          show-icon
          style="margin-top: 8px; font-size: 12px"
        />
      </div>
      <div v-if="cartUsableCoupons.length > 0" class="coupon-select-list">
        <div v-for="c in cartUsableCoupons" :key="c.user_coupon_id"
             class="coupon-select-item"
             :class="{ active: cartSelectedCouponId === c.user_coupon_id }"
             @click="cartSelectedCouponId = cartSelectedCouponId === c.user_coupon_id ? null : c.user_coupon_id">
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
            <div class="cs-desc">满{{ c.min_order_amount }}元可用 · 额外优惠 ¥{{ c.estimated_discount.toFixed(2) }}（折上折）</div>
          </div>
          <el-icon v-if="cartSelectedCouponId === c.user_coupon_id" class="cs-check"><Select /></el-icon>
        </div>
      </div>
      <el-empty v-else description="暂无可用优惠券" :image-size="60" />
      <div class="order-pay-summary" v-if="cartSelectedCoupon">
        <span>额外券优惠：-¥{{ cartSelectedCoupon.estimated_discount.toFixed(2) }}</span>
        <span class="pay-total" style="font-size:12px;color:var(--el-text-color-secondary)">
          （实付以活动折扣叠加券后为准）
        </span>
      </div>
      <template #footer>
        <el-button @click="couponDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="settling" @click="confirmCartOrder">
          {{ cartSelectedCouponId ? '折上折下单' : '下单（活动价自动计算）' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessageBox } from 'element-plus'
import ElMessage from '@/utils/message'
import { Picture, Delete, ShoppingCart } from '@element-plus/icons-vue'

defineOptions({ name: 'NallTrolley' })

const props = defineProps<{
  searchKeyword?: string
}>()

const router = useRouter()

const getHeaders = () => {
  const token = localStorage.getItem('access_token')
  return token ? { 'access-token': token } : {}
}

const hasToken = computed(() => !!(
  localStorage.getItem('access_token')
))

const Axios = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
})

interface CartItem {
  id: number
  mall_id: number
  shopping_id: number
  specification_id: number
  name: string
  img: string
  price: number
  spec_text: string
  quantity: number
  stock: number
  available: boolean
}

interface SelectedItemSnapshot {
  id: number
  mall_id: number
  shopping_id: number
  specification_id: number
  name: string
  price: number
  quantity: number
}

const list = ref<CartItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const deletingId = ref<number | null>(null)
const updatingId = ref<number | null>(null)
const clearing = ref(false)
const settling = ref(false)
const selectedMap = ref<Record<number, SelectedItemSnapshot>>({})

const searchKeyword = computed(() => (props.searchKeyword || '').trim())

const pageTotalPrice = computed(() =>
  list.value.reduce((sum, item) => sum + item.price * item.quantity, 0)
)

const selectableItemsOnPage = computed(() => list.value.filter((item) => item.available))
const checkedCountOnPage = computed(() =>
  selectableItemsOnPage.value.filter((item) => !!selectedMap.value[item.id]).length
)
const allCheckedOnPage = computed(() =>
  selectableItemsOnPage.value.length > 0 &&
  checkedCountOnPage.value === selectableItemsOnPage.value.length
)
const indeterminateOnPage = computed(() =>
  checkedCountOnPage.value > 0 && checkedCountOnPage.value < selectableItemsOnPage.value.length
)
const selectedList = computed(() => Object.values(selectedMap.value))
const selectedCount = computed(() => selectedList.value.length)
const selectedTotalPrice = computed(() =>
  selectedList.value.reduce((sum, item) => sum + item.price * item.quantity, 0)
)

const toSnapshot = (item: CartItem): SelectedItemSnapshot => ({
  id: item.id,
  mall_id: item.mall_id,
  shopping_id: item.shopping_id,
  specification_id: item.specification_id,
  name: item.name,
  price: item.price,
  quantity: item.quantity,
})

const isItemSelected = (id: number) => !!selectedMap.value[id]

const toggleItemSelected = (item: CartItem, checked: boolean) => {
  if (!item.available) return
  if (checked) {
    selectedMap.value[item.id] = toSnapshot(item)
  } else {
    delete selectedMap.value[item.id]
  }
}

const toggleAllOnPage = (checked: boolean | string | number) => {
  const shouldCheck = !!checked
  for (const item of selectableItemsOnPage.value) {
    if (shouldCheck) {
      selectedMap.value[item.id] = toSnapshot(item)
    } else {
      delete selectedMap.value[item.id]
    }
  }
}

const fetchList = async () => {
  if (!hasToken.value) return
  loading.value = true
  try {
    const params: Record<string, string | number> = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    const res = await Axios.get('/shopping_cart_list', {
      params,
      headers: getHeaders(),
    })
    if (res.data.success) {
      list.value = res.data.data || []
      total.value = res.data.total ?? 0
      for (const item of list.value) {
        if (selectedMap.value[item.id]) {
          selectedMap.value[item.id] = toSnapshot(item)
        }
      }
    } else {
      list.value = []
      total.value = 0
    }
  } catch {
    list.value = []
    total.value = 0
    ElMessage.error('获取购物车失败')
  } finally {
    loading.value = false
  }
}

// 搜索关键词变化时重置到第一页并重新请求
watch(searchKeyword, () => {
  page.value = 1
  if (hasToken.value) fetchList()
})

// 每页条数变化时重置到第一页并重新请求
const onPageSizeChange = () => {
  page.value = 1
  fetchList()
}

const handleQtyChange = async (item: CartItem, newVal: number | undefined) => {
  if (newVal == null || newVal < 1) return
  if (newVal === item.quantity) return
  if (updatingId.value === item.id) return
  updatingId.value = item.id
  try {
    const res = await Axios.patch(
      '/shopping_cart_update',
      { id: item.id, quantity: newVal },
      { headers: getHeaders() }
    )
    if (res.data.success) {
      item.quantity = newVal
      if (selectedMap.value[item.id]) {
        selectedMap.value[item.id] = toSnapshot(item)
      }
      ElMessage.success('已更新')
    } else {
      ElMessage.warning(res.data.msg || '修改失败')
    }
  } catch {
    ElMessage.error('修改失败')
  } finally {
    updatingId.value = null
  }
}

const deleteItem = async (item: CartItem) => {
  try {
    await ElMessageBox.confirm(`确定删除「${item.name}」吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }

  deletingId.value = item.id
  try {
    const res = await Axios.delete('/shopping_cart_delete', {
      params: { id: item.id },
      headers: getHeaders(),
    })
    if (res.data.success) {
      ElMessage.success('已删除')
      list.value = list.value.filter((i) => i.id !== item.id)
      total.value = Math.max(0, total.value - 1)
      delete selectedMap.value[item.id]
    } else {
      ElMessage.warning(res.data.msg || '删除失败')
    }
  } catch {
    ElMessage.error('删除失败')
  } finally {
    deletingId.value = null
  }
}

const clearAll = async () => {
  if (total.value <= 0 || clearing.value) return
  try {
    await ElMessageBox.confirm(
      `确定清空购物车吗？当前共 ${total.value} 件商品`,
      '提示',
      {
        confirmButtonText: '确定清空',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch {
    return
  }

  clearing.value = true
  try {
    const res = await Axios.delete('/shopping_cart_clear', {
      headers: getHeaders(),
    })
    if (res.data.success) {
      ElMessage.success(res.data.msg || '已清空购物车')
      list.value = []
      total.value = 0
      page.value = 1
      selectedMap.value = {}
    } else {
      ElMessage.warning(res.data.msg || '清空失败')
    }
  } catch {
    ElMessage.error('清空失败')
  } finally {
    clearing.value = false
  }
}

/* ── 优惠券相关 ── */
const couponDialogVisible = ref(false)
const cartUsableCoupons = ref<any[]>([])
const cartSelectedCouponId = ref<number | null>(null)
const cartPendingAmount = ref(0)
const cartPendingAddressId = ref<number | null>(null)

const cartSelectedCoupon = computed(() => {
  if (!cartSelectedCouponId.value) return null
  return cartUsableCoupons.value.find((c: any) => c.user_coupon_id === cartSelectedCouponId.value) || null
})

const handleSettle = async () => {
  const items = selectedList.value
  if (items.length === 0) {
    ElMessage.warning('请先勾选要结算的商品')
    return
  }

  const mallIds = new Set(items.map(i => i.mall_id))
  if (mallIds.size > 1) {
    ElMessage.warning('一个订单只能包含同一店铺的商品，请分开结算')
    return
  }

  const token = localStorage.getItem('access_token')
  if (!token) {
    ElMessage.warning('请先登录')
    router.push('/register')
    return
  }

  settling.value = true
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

    const mallId = [...mallIds][0]
    const orderAmount = +items.reduce((sum, i) => sum + i.price * i.quantity, 0).toFixed(2)
    cartPendingAmount.value = orderAmount
    cartPendingAddressId.value = defaultAddrId
    cartSelectedCouponId.value = null

    try {
      const couponRes = await Axios.get('/user_coupon/usable', {
        params: { mall_id: mallId, order_amount: orderAmount },
        headers: getHeaders(),
      })
      cartUsableCoupons.value = couponRes.data?.list || []
    } catch {
      cartUsableCoupons.value = []
    }

    couponDialogVisible.value = true
  } catch {
    ElMessage.error('结算准备失败，请稍后重试')
  } finally {
    settling.value = false
  }
}

const confirmCartOrder = async () => {
  const items = selectedList.value
  if (!cartPendingAddressId.value) return

  settling.value = true
  try {
    const idempotencyKey = `cart_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
    const body: any = {
      items: items.map(i => ({
        mall_id: i.mall_id,
        shopping_id: i.shopping_id,
        specification_id: i.specification_id,
        quantity: i.quantity,
      })),
      address_id: cartPendingAddressId.value,
      idempotency_key: idempotencyKey,
    }
    if (cartSelectedCouponId.value) {
      body.user_coupon_id = cartSelectedCouponId.value
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
      for (const item of items) {
        try {
          await Axios.delete('/shopping_cart_delete', {
            params: { id: item.id },
            headers: getHeaders(),
          })
        } catch { /* ignore */ }
      }
      selectedMap.value = {}
      router.push('/personal_center?tab=orders')
    } else {
      ElMessage.error(orderRes.data?.msg || '下单失败')
    }
  } catch {
    ElMessage.error('结算失败，请稍后重试')
  } finally {
    settling.value = false
  }
}

const goDetail = (item: CartItem) => {
  if (!item.available) return
  router.push(`/commodity/${item.mall_id}/${item.shopping_id}`)
}

const goMall = () => {
  router.push('/mall')
}

onMounted(fetchList)

defineExpose({ fetchList })
</script>

<style scoped lang="scss">
.cart-container {
  padding: 28px 24px;
  max-width: 900px;
  margin: 0 auto;
  min-height: 420px;
  background: var(--color-background);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  border: 1px solid var(--color-border);
}

.cart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

.cart-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cart-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--vt-c-text-light-1);
  letter-spacing: -0.3px;
}

.cart-count {
  font-size: 14px;
  color: var(--vt-c-text-light-2);
}

.cart-loading {
  padding: 48px 0;
}

.router-button {
  text-decoration: none;
}

.empty-hint {
  font-size: 13px;
  color: var(--vt-c-text-light-2);
}

.cart-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cart-select-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 2px;
}

.select-tip {
  font-size: 13px;
  color: var(--vt-c-text-light-2);
}

.cart-item {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 18px 20px;
  background: var(--color-background);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  transition: all 0.35s cubic-bezier(0.25, 0.8, 0.25, 1);
  border: 1px solid var(--color-border);
  opacity: 0;
  animation: fadeInUp 0.5s ease forwards;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    border-color: var(--color-border-hover);
  }

  &--unavailable {
    opacity: 0.65;
  }
}

.item-checkbox {
  flex-shrink: 0;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.item-img {
  position: relative;
  flex-shrink: 0;
  width: 110px;
  height: 110px;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  background: var(--color-background-mute);
  transition: transform 0.3s ease;

  &:hover {
    transform: scale(1.03);
  }

  .img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .img--placeholder {
    display: flex;
    align-items: center;
    justify-content: center;

    .placeholder-icon {
      color: #999;
    }
  }

  .item-img__mask {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.5);
    color: #fff;
    font-size: 13px;
    font-weight: 500;
  }
}

.item-info {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.item-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--vt-c-text-light-1);
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  letter-spacing: -0.2px;
}

.item-spec {
  font-size: 12px;
  color: var(--vt-c-text-light-2);
  margin-bottom: 10px;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
}

.item-price {
  color: #e74c3c;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(231, 76, 60, 0.15);
}

.item-qty-wrap {
  flex-shrink: 0;
}

.qty-input {
  width: 120px;
}

.qty-input :deep(.el-input__inner) {
  text-align: center;
}

.item-tip {
  font-size: 12px;
  color: #e74c3c;
  margin-top: 4px;
}

.item-subtotal {
  font-size: 17px;
  font-weight: 700;
  color: #e74c3c;
  min-width: 90px;
  text-align: right;
  text-shadow: 0 1px 2px rgba(231, 76, 60, 0.2);
}

.item-delete {
  flex-shrink: 0;
}

.cart-pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding: 16px 0;
}

.cart-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 28px;
  padding: 22px 24px;
  background: var(--color-background);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--color-border);
}

.cart-total {
  font-size: 16px;
  color: var(--vt-c-text-light-1);

  .total-price {
    font-size: 22px;
    font-weight: 700;
    color: #e74c3c;
    text-shadow: 0 2px 4px rgba(231, 76, 60, 0.2);
  }
}

.cart-footer-btns {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-settle {
  min-width: 100px;
}

.btn-continue {
  .el-icon {
    margin-right: 6px;
  }
}

/* 暗色模式 */
html.dark .cart-container {
  background: var(--vt-c-black-soft);
  border-color: var(--vt-c-divider-dark-1);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
}

html.dark .cart-header {
  border-bottom-color: var(--vt-c-divider-dark-1);
}

html.dark .cart-title,
html.dark .cart-total {
  color: var(--vt-c-text-dark-1);
}

html.dark .cart-count,
html.dark .empty-hint,
html.dark .select-tip {
  color: var(--vt-c-text-dark-2);
}

html.dark .cart-item {
  background: var(--vt-c-black);
  border-color: var(--vt-c-divider-dark-1);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);

  &:hover {
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
    border-color: var(--vt-c-divider-dark-2);
  }
}

html.dark .cart-footer {
  background: var(--vt-c-black);
  border-color: var(--vt-c-divider-dark-1);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
}

html.dark .item-img {
  background: var(--vt-c-black-mute);
}

html.dark .img--placeholder .placeholder-icon {
  color: var(--vt-c-text-dark-2);
}

html.dark .item-name {
  color: var(--vt-c-text-dark-1);
}

html.dark .item-spec {
  color: var(--vt-c-text-dark-2);
}

html.dark .item-price,
html.dark .item-subtotal,
html.dark .total-price {
  color: #f56c6c;
}

html.dark .item-tip {
  color: #f56c6c;
}

/* 暗色模式 - el-input-number */
html.dark .qty-input :deep(.el-input__wrapper) {
  background: var(--vt-c-black-mute);
  box-shadow: 0 0 0 1px var(--vt-c-divider-dark-1);
}

html.dark .qty-input :deep(.el-input__inner) {
  color: var(--vt-c-text-dark-1);
}

html.dark .qty-input :deep(.el-input-number__decrease),
html.dark .qty-input :deep(.el-input-number__increase) {
  background: var(--vt-c-black-mute);
  border-color: var(--vt-c-divider-dark-1);
  color: var(--vt-c-text-dark-2);
}

html.dark .qty-input :deep(.el-input-number__decrease:hover),
html.dark .qty-input :deep(.el-input-number__increase:hover) {
  color: var(--vt-c-text-dark-1);
}

/* 暗色模式 - el-empty */
html.dark :deep(.el-empty__description) {
  color: var(--vt-c-text-dark-2);
}

/* 优惠券选择弹窗 */
.order-summary { margin-bottom: 12px; font-size: 14px; }
.coupon-select-list { display: flex; flex-direction: column; gap: 8px; max-height: 300px; overflow-y: auto; }
.coupon-select-item { display: flex; align-items: center; border: 2px solid #ebeef5; border-radius: 8px; cursor: pointer; transition: border-color 0.2s; overflow: hidden; }
.coupon-select-item.active { border-color: #409eff; }
.coupon-select-item:hover { border-color: #b3d8ff; }
.cs-left { width: 80px; display: flex; justify-content: center; align-items: baseline; padding: 12px 8px; color: #fff; flex-shrink: 0; }
.cs-bg-full_reduction { background: linear-gradient(135deg, #ff6b6b, #ee5a24); }
.cs-bg-discount { background: linear-gradient(135deg, #4834d4, #6c5ce7); }
.cs-bg-fixed_amount { background: linear-gradient(135deg, #f0932b, #ffbe76); }
.cs-amount { font-size: 22px; font-weight: bold; }
.cs-unit { font-size: 12px; }
.cs-right { flex: 1; padding: 8px 12px; }
.cs-name { font-size: 14px; font-weight: 500; }
.cs-desc { font-size: 12px; color: #999; margin-top: 2px; }
.cs-check { margin-right: 12px; color: #409eff; font-size: 20px; }
.order-pay-summary { display: flex; justify-content: flex-end; gap: 16px; margin-top: 12px; font-size: 14px; }
.pay-total { color: #f56c6c; font-weight: bold; font-size: 16px; }
</style>
