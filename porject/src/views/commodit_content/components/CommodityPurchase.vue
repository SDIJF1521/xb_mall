<template>
  <div class="purchase-panel">

    <!-- 标签 + 名称 -->
    <div class="prod-header">
      <div v-if="props.commodity.type?.length" class="tag-row">
        <span v-for="t in props.commodity.type" :key="t" class="cat-chip">{{ t }}</span>
      </div>
      <h1 class="prod-name">{{ props.commodity.name }}</h1>
    </div>

    <!-- 进入店铺入口 -->
    <div class="store-entry" @click="goToStore">
      <div class="store-entry-left">
        <el-icon class="store-icon"><Shop /></el-icon>
        <span class="store-entry-text">进入店铺</span>
      </div>
      <el-icon class="store-arrow"><ArrowRight /></el-icon>
    </div>

    <div class="divider" />

    <!-- 价格区 -->
    <div class="price-block">
      <div class="price-row">
        <span class="price-label">价格</span>
        <div class="price-main">
          <span class="price-symbol">¥</span>
          <span class="price-int">{{ priceInt }}</span>
          <span class="price-dec">.{{ priceDec }}</span>
        </div>
      </div>
      <div v-if="isSoldOut" class="sold-out-badge">已售罄</div>
    </div>

    <!-- 优惠券领取 -->
    <div v-if="storeCoupons.length" class="coupon-strip">
      <div class="coupon-strip__header">
        <span class="coupon-strip__label">优惠券</span>
        <router-link to="/coupon_center" class="coupon-strip__more">更多 ›</router-link>
      </div>
      <div class="coupon-strip__list">
        <div
          v-for="c in storeCoupons"
          :key="c.id"
          class="coupon-chip"
          :class="[`coupon-chip--${c.coupon_type}`, { 'coupon-chip--disabled': c.claim_status !== 'available' }]"
          @click="c.claim_status === 'available' && claimCoupon(c)"
        >
          <div class="coupon-chip__value">
            <template v-if="c.coupon_type === 'discount'">
              <span class="cv-num">{{ c.discount_value }}</span><span class="cv-unit">折</span>
            </template>
            <template v-else>
              <span class="cv-unit">¥</span><span class="cv-num">{{ c.discount_value }}</span>
            </template>
          </div>
          <div class="coupon-chip__info">
            <span class="coupon-chip__name">{{ c.name }}</span>
            <span class="coupon-chip__cond">满{{ c.min_order_amount }}可用</span>
          </div>
          <span
            class="coupon-chip__btn"
            :class="{
              'is-claiming': claimingId === c.id,
              'is-claimed': c.claim_status === 'claimed',
              'is-sold-out': c.claim_status === 'sold_out',
            }"
          >
            <template v-if="claimingId === c.id">...</template>
            <template v-else-if="c.claim_status === 'claimed'">已领取</template>
            <template v-else-if="c.claim_status === 'sold_out'">已领完</template>
            <template v-else>领取</template>
          </span>
        </div>
      </div>
    </div>

    <div class="divider" />

    <!-- 规格选择 -->
    <div v-if="props.commodity.specification_list?.length" class="spec-block">
      <div class="row-label">规格</div>
      <div class="spec-grid">
        <button
          v-for="(spec, idx) in props.commodity.specification_list"
          :key="idx"
          class="spec-chip"
          :class="{ active: selectedSpecIndex === idx, out: spec.stock === 0 }"
          :disabled="spec.stock === 0"
          @click="selectedSpecIndex = idx"
        >
          <span class="sc-name">{{ spec.specs?.join(' · ') || '—' }}</span>
          <span class="sc-price">¥{{ spec.price }}</span>
          <div v-if="spec.stock === 0" class="sc-mask">售罄</div>
        </button>
      </div>
    </div>

    <!-- 数量 -->
    <div class="qty-block">
      <div class="row-label">数量</div>
      <div class="qty-row">
        <el-input-number
          v-model="quantity"
          :min="1"
          :max="selectedSpec?.stock ?? 999"
          controls-position="right"
          class="qty-input"
        />
        <span v-if="selectedSpec" class="stock-text">
          仅剩 <b>{{ selectedSpec.stock }}</b> 件
        </span>
      </div>
    </div>

    <div class="divider" />

    <!-- 操作按钮 -->
    <div class="action-group">
      <el-button
        class="btn-buy"
        :disabled="isSoldOut"
        :loading="props.buyLoading"
        @click="handleBuy"
      >
        <el-icon><Lightning /></el-icon>
        立即购买
      </el-button>
      <el-button
        class="btn-cart"
        :disabled="isSoldOut"
        :loading="props.cartLoading"
        @click="handleAddToCart"
      >
        <el-icon><ShoppingCart /></el-icon>
        加入购物车
      </el-button>
      <button
        class="btn-wish"
        :class="{ wished: props.isWishlisted }"
        @click="emit('wishlist')"
      >
        <el-icon><Star /></el-icon>
      </button>
    </div>

    <!-- 服务保障条 -->
    <div class="guarantee-row">
      <div class="g-item">
        <el-icon><Medal /></el-icon>
        <span>正品保证</span>
      </div>
      <div class="g-sep" />
      <div class="g-item">
        <el-icon><Van /></el-icon>
        <span>极速发货</span>
      </div>
      <div class="g-sep" />
      <div class="g-item">
        <el-icon><RefreshLeft /></el-icon>
        <span>7天退换</span>
      </div>
      <div class="g-sep" />
      <div class="g-item g-item--clickable" @click="emit('service')">
        <el-icon><Service /></el-icon>
        <span>联系客服</span>
      </div>
    </div>

    <!-- 联系客服按钮 -->
    <button class="btn-service" @click="emit('service')">
      <el-icon><Service /></el-icon>
      联系客服
    </button>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { ShoppingCart, Star, Van, RefreshLeft, Medal, Service, Shop, ArrowRight } from '@element-plus/icons-vue'
import { Lightning } from '@element-plus/icons-vue'

interface Spec {
  specs: string[]
  price: number
  stock: number
  specification_id?: number
}
interface Commodity {
  name: string
  price: number
  type: string[]
  specification_list?: Spec[]
  shopping_id?: number
}

const props = defineProps<{
  commodity: Commodity
  mallId: number
  buyLoading?: boolean
  cartLoading?: boolean
  wishlistLoading?: boolean
  isWishlisted?: boolean
}>()

const router = useRouter()
const goToStore = () => router.push(`/store/${props.mallId}`)

const emit = defineEmits<{
  (e: 'buy', payload: { specIndex: number; quantity: number }): void
  (e: 'add-to-cart', payload: { specIndex: number; quantity: number }): void
  (e: 'wishlist'): void
  (e: 'service'): void
}>()

const selectedSpecIndex = ref(0)
const quantity = ref(1)

const selectedSpec = computed<Spec | undefined>(
  () => props.commodity.specification_list?.[selectedSpecIndex.value]
)

const currentPrice = computed(
  () => selectedSpec.value?.price ?? props.commodity.price ?? 0
)

const priceInt = computed(() => Math.floor(currentPrice.value))
const priceDec = computed(() => {
  const dec = (currentPrice.value - Math.floor(currentPrice.value)).toFixed(2).slice(2)
  return dec
})

const isSoldOut = computed(() => {
  if (!props.commodity.specification_list?.length) return false
  return (selectedSpec.value?.stock ?? 0) === 0
})

const handleBuy = () => emit('buy', { specIndex: selectedSpecIndex.value, quantity: quantity.value })
const handleAddToCart = () => emit('add-to-cart', { specIndex: selectedSpecIndex.value, quantity: quantity.value })

const API = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const storeCoupons = ref<any[]>([])
const claimingId = ref<number | null>(null)

async function loadStoreCoupons() {
  try {
    const params: Record<string, any> = {
      mall_id: props.mallId,
      page: 1,
      page_size: 6,
    }
    if (props.commodity.shopping_id) {
      params.shopping_id = props.commodity.shopping_id
    }
    const token = localStorage.getItem('access_token')
    const reqHeaders: Record<string, string> = {}
    if (token) reqHeaders['access-token'] = token
    const { data } = await API.get('/user_coupon/available', { params, headers: reqHeaders })
    if (data.success) {
      storeCoupons.value = data.list || []
    }
  } catch { /* ignore */ }
}

async function claimCoupon(c: any) {
  const token = localStorage.getItem('access_token')
  if (!token) {
    ElMessage.warning('请先登录后领取')
    router.push('/register')
    return
  }
  claimingId.value = c.id
  try {
    const { data } = await API.post(
      '/user_coupon/claim',
      { coupon_id: c.id },
      { headers: { 'access-token': token } },
    )
    if (data.success) {
      ElMessage.success('领取成功')
      await loadStoreCoupons()
    } else {
      ElMessage.warning(data.msg || '领取失败')
    }
  } catch {
    ElMessage.error('领取失败')
  } finally {
    claimingId.value = null
  }
}

onMounted(() => {
  loadStoreCoupons()
})
</script>

<style scoped lang="scss">
.purchase-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.divider {
  height: 1px;
  background: var(--color-border);
  margin: 0 -28px;
}

/* ── 标题 ── */
.prod-header {
  .tag-row {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 10px;
  }

  .cat-chip {
    display: inline-flex;
    align-items: center;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    background: linear-gradient(135deg, #667eea22, #764ba222);
    color: #667eea;
    border: 1px solid #667eea44;
    letter-spacing: 0.3px;
  }

  .prod-name {
    font-size: 22px;
    font-weight: 700;
    color: var(--color-heading);
    line-height: 1.45;
    margin: 0;
    letter-spacing: -0.3px;
  }
}

/* ── 价格 ── */
.price-block {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .price-row {
    display: flex;
    align-items: baseline;
    gap: 16px;
  }

  .price-label {
    font-size: 13px;
    color: var(--el-text-color-placeholder);
    flex-shrink: 0;
  }

  .price-main {
    display: flex;
    align-items: baseline;
    gap: 1px;
    color: #e74c3c;
  }

  .price-symbol {
    font-size: 18px;
    font-weight: 600;
    line-height: 1;
  }

  .price-int {
    font-size: 42px;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -1px;
  }

  .price-dec {
    font-size: 20px;
    font-weight: 600;
    line-height: 1;
    align-self: flex-end;
    margin-bottom: 4px;
  }

  .sold-out-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 12px;
    border-radius: 6px;
    background: var(--el-fill-color);
    color: var(--el-text-color-placeholder);
    font-size: 13px;
    font-weight: 600;
    border: 1px solid var(--el-border-color);
  }
}

/* ── 优惠券条 ── */
.coupon-strip {
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }

  &__label {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    font-weight: 500;
  }

  &__more {
    font-size: 12px;
    color: var(--el-color-primary);
    text-decoration: none;
    &:hover { text-decoration: underline; }
  }

  &__list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
}

.coupon-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px 6px 0;
  border-radius: 8px;
  border: 1.5px solid;
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;

  &--full_reduction {
    border-color: #ff6b6b44;
    &:hover { border-color: #ff6b6b; background: #ff6b6b08; }
  }
  &--discount {
    border-color: #6c5ce744;
    &:hover { border-color: #6c5ce7; background: #6c5ce708; }
  }
  &--fixed_amount {
    border-color: #f0932b44;
    &:hover { border-color: #f0932b; background: #f0932b08; }
  }

  &__value {
    display: flex;
    align-items: baseline;
    padding: 4px 8px;
    border-radius: 6px 0 0 6px;
    color: #fff;
    min-width: 48px;
    justify-content: center;

    .cv-num { font-size: 16px; font-weight: 800; line-height: 1; }
    .cv-unit { font-size: 10px; font-weight: 600; }
  }

  &--full_reduction &__value { background: linear-gradient(135deg, #ff6b6b, #ee5a24); }
  &--discount &__value { background: linear-gradient(135deg, #4834d4, #6c5ce7); }
  &--fixed_amount &__value { background: linear-gradient(135deg, #f0932b, #ffbe76); }

  &__info {
    display: flex;
    flex-direction: column;
    gap: 1px;
    min-width: 0;
  }

  &__name {
    font-size: 12px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 100px;
  }

  &__cond {
    font-size: 10px;
    color: var(--el-text-color-placeholder);
  }

  &__btn {
    font-size: 11px;
    font-weight: 700;
    color: #fff;
    background: linear-gradient(135deg, #667eea, #764ba2);
    padding: 3px 10px;
    border-radius: 20px;
    white-space: nowrap;
    flex-shrink: 0;
    transition: all 0.2s;

    &:hover:not(.is-claimed):not(.is-sold-out) {
      transform: scale(1.05);
      box-shadow: 0 2px 8px rgba(102,126,234,0.4);
    }
    &.is-claiming { opacity: 0.6; pointer-events: none; }
    &.is-claimed {
      background: #95a5a6;
      cursor: default;
    }
    &.is-sold-out {
      background: #bdc3c7;
      cursor: default;
    }
  }

  &--disabled {
    opacity: 0.7;
    cursor: default !important;
  }
}

/* ── 规格 ── */
.row-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 10px;
  font-weight: 500;
}

.spec-block { }

.spec-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.spec-chip {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 3px;
  padding: 10px 16px 10px 14px;
  border-radius: 10px;
  border: 1.5px solid var(--el-border-color);
  background: var(--el-bg-color);
  cursor: pointer;
  transition: all 0.18s ease;
  overflow: hidden;
  min-width: 90px;

  &:hover:not(.out) {
    border-color: #667eea;
    background: rgba(102,126,234,0.04);
  }

  &.active {
    border-color: #667eea;
    background: rgba(102,126,234,0.06);

    &::after {
      content: '✓';
      position: absolute;
      top: -1px;
      right: -1px;
      width: 18px;
      height: 18px;
      background: #667eea;
      border-radius: 0 10px 0 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      color: #fff;
      line-height: 18px;
      text-align: center;
    }

    .sc-name { color: #667eea; font-weight: 600; }
    .sc-price { color: #764ba2; }
  }

  &.out {
    cursor: not-allowed;
    opacity: 0.4;
  }

  .sc-name {
    font-size: 14px;
    color: var(--el-text-color-primary);
    font-weight: 500;
  }

  .sc-price {
    font-size: 12px;
    color: var(--el-color-danger);
  }

  .sc-mask {
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(
      -45deg,
      transparent,
      transparent 4px,
      rgba(0,0,0,0.04) 4px,
      rgba(0,0,0,0.04) 8px
    );
  }
}

/* ── 数量 ── */
.qty-block { }

.qty-row {
  display: flex;
  align-items: center;
  gap: 14px;

  .qty-input {
    width: 140px;
  }

  .stock-text {
    font-size: 13px;
    color: var(--el-text-color-placeholder);

    b {
      color: #e67e22;
      font-weight: 700;
    }
  }
}

/* ── 按钮组 ── */
.action-group {
  display: flex;
  gap: 10px;
  align-items: stretch;

  .btn-buy {
    flex: 1.2;
    height: 50px;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    color: #fff;
    letter-spacing: 0.5px;
    transition: all 0.25s ease;

    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(102,126,234,0.5);
    }
    &:active:not(:disabled) { transform: translateY(0); }
  }

  .btn-cart {
    flex: 1;
    height: 50px;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 600;
    background: var(--el-bg-color);
    border: 1.5px solid #667eea;
    color: #667eea;
    transition: all 0.25s ease;

    &:hover:not(:disabled) {
      background: rgba(102,126,234,0.06);
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(102,126,234,0.2);
    }
  }

  .btn-wish {
    width: 50px;
    height: 50px;
    border-radius: 12px;
    border: 1.5px solid var(--el-border-color);
    background: var(--el-bg-color);
    color: var(--el-text-color-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    cursor: pointer;
    transition: all 0.25s ease;
    flex-shrink: 0;

    &:hover {
      border-color: #e74c3c;
      color: #e74c3c;
      transform: scale(1.08);
    }

    &.wished {
      background: linear-gradient(135deg, #ff6b6b, #ee5a24);
      border-color: transparent;
      color: #fff;
    }
  }
}

/* ── 进入店铺 ── */
.store-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-radius: 10px;
  border: 1px solid var(--el-border-color);
  background: var(--color-background-soft);
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: #667eea;
    background: rgba(102, 126, 234, 0.05);

    .store-icon,
    .store-entry-text,
    .store-arrow { color: #667eea; }
  }
}

.store-entry-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.store-icon {
  font-size: 18px;
  color: var(--el-text-color-secondary);
  transition: color 0.2s;
}

.store-entry-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  transition: color 0.2s;
}

.store-arrow {
  font-size: 14px;
  color: var(--el-text-color-placeholder);
  transition: color 0.2s;
}

/* ── 保障条 ── */
.guarantee-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-radius: 12px;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
}

.g-sep {
  width: 1px;
  height: 24px;
  background: var(--color-border);
}

.g-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--el-text-color-secondary);
  font-weight: 500;

  .el-icon {
    font-size: 20px;
    color: #667eea;
  }

  &--clickable {
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 8px;
    transition: all 0.2s;

    &:hover {
      background: rgba(102, 126, 234, 0.1);
      color: #667eea;
    }
  }
}

/* ── 联系客服按钮 ── */
.btn-service {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 44px;
  border-radius: 12px;
  border: 1.5px solid #667eea;
  background: rgba(102, 126, 234, 0.06);
  color: #667eea;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;

  .el-icon { font-size: 16px; }

  &:hover {
    background: rgba(102, 126, 234, 0.12);
    border-color: #764ba2;
    color: #764ba2;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
  }

  &:active { transform: translateY(0); }
}
</style>
