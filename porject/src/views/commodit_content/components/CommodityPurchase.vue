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
      <div class="g-item">
        <el-icon><Service /></el-icon>
        <span>在线客服</span>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
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
}
</style>
