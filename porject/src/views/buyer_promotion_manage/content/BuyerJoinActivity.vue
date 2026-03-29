<template>
  <div class="join-activity">
    <div class="section-header">
      <h3>可参加的平台活动</h3>
      <el-button :icon="Refresh" circle @click="loadList(page)" />
    </div>

    <div v-if="loading" class="loading-box"><el-skeleton :rows="4" animated /></div>
    <div v-else-if="list.length === 0" class="empty-box"><el-empty description="暂无可参加的平台活动" /></div>
    <div v-else>
      <div class="activity-cards">
        <el-card v-for="item in list" :key="item.id" class="activity-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="card-title-row">
                <el-tag size="small" :type="actTypeTag(item.activity_type)">{{ actTypeLabel(item.activity_type) }}</el-tag>
                <span class="card-name">{{ item.name }}</span>
              </div>
              <div class="card-header-right">
                <el-tag size="small" type="success" style="margin-left: 4px">进行中</el-tag>
              </div>
            </div>
          </template>
          <div class="card-body">
            <div class="card-info">
              <div class="info-row">
                <span class="label">活动时间：</span>
                <span>{{ item.start_time?.slice(0, 16) }} 至 {{ item.end_time?.slice(0, 16) }}</span>
              </div>
              <div v-if="item.description" class="info-row">
                <span class="label">活动说明：</span>
                <span>{{ item.description }}</span>
              </div>
              <div class="info-row">
                <span class="label">活动规则：</span>
                <span class="rules-text">{{ formatRules(item.activity_type, item.rules) }}</span>
              </div>
              <div v-if="isRulePricedType(item.activity_type)" class="info-row">
                <span class="label">折扣叠加：</span>
                <span :class="item.rules?.stackable ? 'stackable-yes' : 'stackable-no'">
                  {{ item.rules?.stackable ? '✓ 活动价可叠加优惠券（折上折）' : '✗ 活动期间不可叠加其他折扣' }}
                </span>
              </div>
            </div>
            <div class="card-actions">
              <el-button type="primary" size="small" @click="openJoinDialog(item)">选择商品加入</el-button>
              <el-button size="small" plain @click="openLeaveDialog(item)">退出活动</el-button>
            </div>
          </div>
        </el-card>
      </div>
      <div class="pager">
        <el-pagination :page-size="pageSize" layout="total, prev, pager, next" :total="total" :current-page="page" @current-change="loadList" />
      </div>
    </div>

    <!-- 加入活动对话框：从本店商品中选择 -->
    <el-dialog v-model="joinVisible" title="选择商品加入活动" width="780px" destroy-on-close @open="loadMyProducts(1)">
      <el-alert v-if="currentActivity" :title="`即将加入：${currentActivity.name}`" type="info" :closable="false" style="margin-bottom: 10px" />

      <!-- 活动定价规则提示 -->
      <template v-if="joinPriceMode === 'rule'">
        <el-alert
          v-if="!joinStackable"
          :title="`${joinActivityTypeLabel}活动，按 ${joinDiscountRate} 折计算，不可叠加其他折扣`"
          type="warning"
          :closable="false"
          show-icon
          style="margin-bottom: 8px"
        />
        <el-alert
          v-else
          :title="`${joinActivityTypeLabel}活动，按 ${joinDiscountRate} 折计算，✓ 支持叠加优惠券（折上折）`"
          type="success"
          :closable="false"
          show-icon
          style="margin-bottom: 8px"
        />
        <div v-if="joinStackable" class="stacked-rate-row">
          <template v-if="couponsLoading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span class="stacked-rate-label">正在读取店铺优惠券…</span>
          </template>
          <template v-else-if="storeBestCoupon || productCouponMap.size > 0">
            <el-icon style="color: var(--el-color-success)"><CircleCheck /></el-icon>
            <span class="stacked-rate-label">
              已读取折扣优惠券，将按商品最优券自动估算折上折价
            </span>
            <el-tag v-if="storeBestCoupon" size="small" type="success">
              {{ storeBestCoupon.name }}（{{ (storeBestCoupon.rate * 10).toFixed(1) }}折）通用
            </el-tag>
            <el-tag v-if="productCouponMap.size > 0" size="small" type="warning">
              另有 {{ productCouponMap.size }} 款商品专属券
            </el-tag>
          </template>
          <template v-else>
            <el-icon style="color: var(--el-text-color-placeholder)"><InfoFilled /></el-icon>
            <span class="stacked-rate-hint">暂无可叠加的折扣优惠券，无法展示折上折估算</span>
          </template>
        </div>
      </template>
      <el-alert
        v-else-if="joinPriceMode === 'cart'"
        title="满减活动为购物车级别折扣，商品本身价格不变，选择商品加入即可"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 10px"
      />

      <div style="display: flex; gap: 8px; margin-bottom: 14px">
        <el-input
          v-model="productSearch"
          placeholder="搜索商品名称"
          clearable
          style="flex: 1"
          @input="loadMyProducts(1)"
        />
        <el-button :icon="Refresh" @click="loadMyProducts(productPage)" />
      </div>

      <div v-if="productsLoading" style="padding: 32px 0; text-align: center">
        <el-skeleton :rows="5" animated />
      </div>
      <div v-else-if="myProducts.length === 0" style="padding: 24px 0">
        <el-empty description="暂无可加入的商品" />
      </div>
      <div v-else class="product-list">
        <div v-for="prod in myProducts" :key="prod.shopping_id" class="product-block">
          <!-- 无规格商品 -->
          <template v-if="!prod.specifications || prod.specifications.length === 0">
            <div class="product-row" :class="{ disabled: prod.already_joined }">
              <el-checkbox
                v-model="prod._selected"
                :disabled="prod.already_joined"
              />
              <el-image
                v-if="prod.img"
                :src="`data:image/jpeg;base64,${prod.img}`"
                class="prod-thumb"
                fit="cover"
              />
              <div v-else class="prod-thumb-placeholder" />
              <span class="prod-name">{{ prod.name }}</span>
              <template v-if="prod._selected && joinPriceMode === 'free'">
                <el-input-number
                  v-model="prod._price"
                  :min="0.01"
                  :precision="2"
                  :controls="false"
                  placeholder="活动价(选填)"
                  size="small"
                  class="price-input"
                />
                <el-input-number
                  v-model="prod._stock"
                  :min="1"
                  :controls="false"
                  placeholder="库存限制(选填)"
                  size="small"
                  class="stock-input"
                />
              </template>
              <template v-else-if="prod._selected && joinPriceMode === 'rule'">
                <div class="rule-price-col">
                  <span class="rule-price-hint">活动价约 ¥{{ calcRulePrice(prod.specifications?.[0]?.price ?? 0) }}</span>
                  <template v-if="joinStackable">
                    <span v-if="getStackedInfo(prod.shopping_id)" class="rule-stacked-hint">
                      折上折约 ¥{{ calcStackedPrice(prod.specifications?.[0]?.price ?? 0, prod.shopping_id) }}
                      <span class="stacked-coupon-tag">{{ getStackedInfo(prod.shopping_id)!.name }}</span>
                    </span>
                    <span v-else-if="!couponsLoading" class="no-stack-hint">无可叠加优惠</span>
                  </template>
                </div>
              </template>
              <el-tag v-if="prod.already_joined" type="success" size="small" style="margin-left: auto">已加入</el-tag>
            </div>
          </template>

          <!-- 有规格商品 -->
          <template v-else>
            <div class="product-header-row">
              <el-image
                v-if="prod.img"
                :src="`data:image/jpeg;base64,${prod.img}`"
                class="prod-thumb"
                fit="cover"
              />
              <div v-else class="prod-thumb-placeholder" />
              <span class="prod-name"><strong>{{ prod.name }}</strong></span>
            </div>
            <div
              v-for="spec in prod.specifications"
              :key="spec.specification_id"
              class="spec-row"
              :class="{ disabled: spec.already_joined }"
            >
              <el-checkbox
                v-model="spec._selected"
                :disabled="spec.already_joined"
              />
              <span class="spec-name">{{ spec.name || `规格${spec.specification_id}` }}</span>
              <span class="spec-origin-price">原价 ¥{{ spec.price }}</span>
              <template v-if="spec._selected && joinPriceMode === 'free'">
                <el-input-number
                  v-model="spec._price"
                  :min="0.01"
                  :precision="2"
                  :controls="false"
                  placeholder="活动价(选填)"
                  size="small"
                  class="price-input"
                />
                <el-input-number
                  v-model="spec._stock"
                  :min="1"
                  :controls="false"
                  placeholder="库存限制(选填)"
                  size="small"
                  class="stock-input"
                />
              </template>
              <template v-else-if="spec._selected && joinPriceMode === 'rule'">
                <div class="rule-price-col">
                  <span class="rule-price-hint">活动价约 ¥{{ calcRulePrice(spec.price) }}</span>
                  <template v-if="joinStackable">
                    <span v-if="getStackedInfo(prod.shopping_id)" class="rule-stacked-hint">
                      折上折约 ¥{{ calcStackedPrice(spec.price, prod.shopping_id) }}
                      <span class="stacked-coupon-tag">{{ getStackedInfo(prod.shopping_id)!.name }}</span>
                    </span>
                    <span v-else-if="!couponsLoading" class="no-stack-hint">无可叠加优惠</span>
                  </template>
                </div>
              </template>
              <el-tag v-if="spec.already_joined" type="success" size="small" style="margin-left: auto">已加入</el-tag>
            </div>
          </template>
        </div>
      </div>

      <el-pagination
        v-if="productTotal > productPageSize"
        :page-size="productPageSize"
        layout="prev, pager, next"
        :total="productTotal"
        :current-page="productPage"
        @current-change="loadMyProducts"
        style="margin-top: 12px; justify-content: flex-end"
      />

      <template #footer>
        <el-button @click="joinVisible = false">取消</el-button>
        <el-button type="primary" :loading="joinSubmitting" @click="submitJoin">确认加入</el-button>
      </template>
    </el-dialog>

    <!-- 退出活动对话框：从已加入商品中勾选 -->
    <el-dialog v-model="leaveVisible" title="退出平台活动" width="600px" destroy-on-close @open="loadJoinedProducts">
      <el-alert v-if="currentActivity" :title="`即将退出：${currentActivity.name}`" type="warning" :closable="false" style="margin-bottom: 14px" />

      <el-radio-group v-model="leaveMode" style="margin-bottom: 16px">
        <el-radio value="all">退出全部商品</el-radio>
        <el-radio value="partial">退出指定商品</el-radio>
      </el-radio-group>

      <template v-if="leaveMode === 'partial'">
        <div v-if="leaveProductsLoading" style="padding: 20px 0">
          <el-skeleton :rows="3" animated />
        </div>
        <div v-else-if="joinedProducts.length === 0" style="padding: 16px 0">
          <el-empty description="该活动暂无已加入的商品" />
        </div>
        <div v-else class="leave-product-list">
          <div
            v-for="prod in joinedProducts"
            :key="prod.shopping_id"
            class="leave-product-row"
          >
            <el-checkbox v-model="prod._leave" />
            <el-image
              v-if="prod.img"
              :src="`data:image/jpeg;base64,${prod.img}`"
              class="prod-thumb"
              fit="cover"
            />
            <div v-else class="prod-thumb-placeholder" />
            <span class="prod-name">{{ prod.name }}</span>
          </div>
        </div>
      </template>

      <template #footer>
        <el-button @click="leaveVisible = false">取消</el-button>
        <el-button type="warning" :loading="leaveSubmitting" @click="submitLeave">确认退出</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Refresh, Loading, CircleCheck, InfoFilled } from '@element-plus/icons-vue'

defineOptions({ name: 'BuyerJoinActivity' })

const props = defineProps<{ mallId?: number | null }>()

const API = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const token = localStorage.getItem('buyer_access_token') || ''
const headers = { 'access-token': token }

function mallParam(): Record<string, any> {
  return props.mallId ? { mall_id: props.mallId } : {}
}

// ───── 平台活动列表 ─────
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const currentActivity = ref<any>(null)

// ───── 加入对话框 ─────
const joinVisible = ref(false)
const joinSubmitting = ref(false)
const myProducts = ref<any[]>([])
const productsLoading = ref(false)
const productSearch = ref('')
const productPage = ref(1)
const productPageSize = ref(10)
const productTotal = ref(0)

// ───── 退出对话框 ─────
const leaveVisible = ref(false)
const leaveSubmitting = ref(false)
const leaveMode = ref<'all' | 'partial'>('all')
const joinedProducts = ref<any[]>([])
const leaveProductsLoading = ref(false)

// ───── 工具函数 ─────
function actTypeLabel(t: string) {
  return { flash_sale: '秒杀', full_reduction: '满减', discount: '折扣', group_buy: '拼团' }[t] || t
}
function actTypeTag(t: string) {
  return { flash_sale: 'danger', full_reduction: 'warning', discount: 'success', group_buy: '' }[t] || 'info'
}

/** 当前加入活动的定价模式：rule=规则折扣 | cart=购物车满减 | free=商家自设 */
const joinPriceMode = computed<'rule' | 'cart' | 'free'>(() => {
  const t = currentActivity.value?.activity_type
  if (t === 'full_reduction') return 'cart'
  if (t === 'flash_sale' || t === 'discount' || t === 'group_buy') return 'rule'
  return 'free'
})
const joinActivityTypeLabel = computed(() => actTypeLabel(currentActivity.value?.activity_type ?? ''))
const joinDiscountRate = computed(() => {
  const rules = currentActivity.value?.rules
  if (!rules) return '-'
  const dr = rules.discount_rate
  return dr != null ? (dr * 10).toFixed(1) : '-'
})

/** 当前活动是否支持叠加优惠券折扣 */
const joinStackable = computed(() => !!currentActivity.value?.rules?.stackable)

/** 判断活动类型是否属于折扣率定价类型 */
function isRulePricedType(type: string): boolean {
  return ['flash_sale', 'discount', 'group_buy'].includes(type)
}

/** 按 discount_rate 估算活动折后价 */
function calcRulePrice(originalPrice: number): string {
  const rules = currentActivity.value?.rules
  const dr = rules?.discount_rate
  if (dr == null || !originalPrice) return '-'
  return (originalPrice * dr).toFixed(2)
}

// ───── 折上折：自动读取店铺优惠券 ─────

interface CouponStackInfo {
  rate: number    // discount_value，如 0.9 表示九折
  name: string
}

const storeBestCoupon = ref<CouponStackInfo | null>(null)
const productCouponMap = ref<Map<number, CouponStackInfo>>(new Map())
const couponsLoading = ref(false)

/** 拉取本店活动中的 discount 类型优惠券，构建商品 → 最优折扣映射 */
async function loadStoreCoupons() {
  if (!joinStackable.value) return
  couponsLoading.value = true
  storeBestCoupon.value = null
  productCouponMap.value = new Map()
  try {
    const { data } = await API.get('/buyer_coupon/list', {
      params: { status: 'active', page: 1, page_size: 100, ...mallParam() },
      headers,
    })
    if (!data.current) return

    // 只保留折扣率类型优惠券（discount_value 是小于 1 的折扣率）
    const discountCoupons: any[] = (data.list || []).filter(
      (c: any) => c.coupon_type === 'discount' && c.discount_value > 0 && c.discount_value < 1,
    )

    // 店铺通用优惠券（scope = all_mall 或 store）
    const storeWide = discountCoupons.filter(
      (c: any) => c.scope === 'all_mall' || c.scope === 'store',
    )
    const bestSW = storeWide.reduce<any>(
      (best, c) => (!best || c.discount_value < best.discount_value) ? c : best,
      null,
    )
    if (bestSW) {
      storeBestCoupon.value = { rate: bestSW.discount_value, name: bestSW.name }
    }

    // 商品专属优惠券（scope = product）：逐一拉取详情获取关联 shopping_id
    const productScoped = discountCoupons.filter((c: any) => c.scope === 'product')
    const newMap = new Map<number, CouponStackInfo>()
    await Promise.all(
      productScoped.map(async (coupon: any) => {
        try {
          const { data: det } = await API.get('/buyer_coupon/detail', {
            params: { coupon_id: coupon.id, ...mallParam() },
            headers,
          })
          if (det.current && det.data?.products) {
            for (const p of det.data.products) {
              const existing = newMap.get(p.shopping_id)
              if (!existing || coupon.discount_value < existing.rate) {
                newMap.set(p.shopping_id, { rate: coupon.discount_value, name: coupon.name })
              }
            }
          }
        } catch { /* 单券详情失败不影响其他 */ }
      }),
    )
    productCouponMap.value = newMap
  } catch {
    // 拉取失败时静默处理，折上折区域将显示"无可叠加优惠"
  } finally {
    couponsLoading.value = false
  }
}

/** 获取某商品最佳可叠加优惠券（商品专属 > 店铺通用，折扣越大优先） */
function getStackedInfo(shoppingId: number): CouponStackInfo | null {
  if (!joinStackable.value) return null
  const productSpecific = productCouponMap.value.get(shoppingId)
  const storeWide = storeBestCoupon.value
  if (!productSpecific && !storeWide) return null
  if (!productSpecific) return storeWide
  if (!storeWide) return productSpecific
  return productSpecific.rate <= storeWide.rate ? productSpecific : storeWide
}

/** 计算折上折最终估算价 = 原价 × 活动折扣率 × 优惠券折扣率 */
function calcStackedPrice(originalPrice: number, shoppingId: number): string {
  const info = getStackedInfo(shoppingId)
  if (!info || !originalPrice) return ''
  const dr = currentActivity.value?.rules?.discount_rate
  if (dr == null) return ''
  return (originalPrice * dr * info.rate).toFixed(2)
}
function formatRules(type: string, rules: any) {
  if (!rules) return '-'
  if (type === 'flash_sale') return `折扣率 ${rules.discount_rate ?? '-'}`
  if (type === 'discount') return `折扣率 ${rules.discount_rate ?? '-'}`
  if (type === 'full_reduction' && rules.thresholds) {
    return rules.thresholds.map((t: any) => `满${t.min_amount}减${t.reduction}`).join('，')
  }
  if (type === 'group_buy') return `${rules.min_group_size}人成团，折扣率 ${rules.discount_rate}`
  return JSON.stringify(rules)
}

// ───── 平台活动列表加载 ─────
async function loadList(p: number) {
  loading.value = true
  page.value = p
  try {
    const { data } = await API.get('/buyer_activity/joinable', {
      params: { page: p, page_size: pageSize.value, ...mallParam() },
      headers,
    })
    if (data.current) {
      list.value = data.list
      total.value = data.total
    } else {
      ElMessage.warning(data.msg)
    }
  } catch {
    ElMessage.error('获取平台活动失败')
  } finally {
    loading.value = false
  }
}

// ───── 加入对话框：加载本店商品 ─────
function openJoinDialog(activity: any) {
  currentActivity.value = activity
  productSearch.value = ''
  productPage.value = 1
  myProducts.value = []
  storeBestCoupon.value = null
  productCouponMap.value = new Map()
  joinVisible.value = true
  loadStoreCoupons()
}

async function loadMyProducts(p: number) {
  if (!currentActivity.value) return
  productsLoading.value = true
  productPage.value = p
  try {
    const { data } = await API.get('/buyer_activity/my_products', {
      params: {
        activity_id: currentActivity.value.id,
        page: p,
        page_size: productPageSize.value,
        search: productSearch.value,
        ...mallParam(),
      },
      headers,
    })
    if (data.current) {
      // 为每个商品及规格附加响应式选中状态
      myProducts.value = (data.data || []).map((prod: any) => ({
        ...prod,
        _selected: false,
        _price: undefined,
        _stock: undefined,
        specifications: (prod.specifications || []).map((sp: any) => ({
          ...sp,
          _selected: false,
          _price: undefined,
          _stock: undefined,
        })),
      }))
      productTotal.value = data.total
    } else {
      ElMessage.warning(data.msg)
    }
  } catch {
    ElMessage.error('获取商品列表失败')
  } finally {
    productsLoading.value = false
  }
}

async function submitJoin() {
  const products: any[] = []

  for (const prod of myProducts.value) {
    if (prod.specifications && prod.specifications.length > 0) {
      for (const sp of prod.specifications) {
        if (sp._selected) {
          products.push({
            shopping_id: prod.shopping_id,
            specification_id: sp.specification_id,
            activity_price: sp._price ?? undefined,
            activity_stock: sp._stock ?? undefined,
          })
        }
      }
    } else if (prod._selected) {
      products.push({
        shopping_id: prod.shopping_id,
        specification_id: undefined,
        activity_price: prod._price ?? undefined,
        activity_stock: prod._stock ?? undefined,
      })
    }
  }

  if (products.length === 0) {
    ElMessage.warning('请至少选择一个商品')
    return
  }

  joinSubmitting.value = true
  try {
    const { data } = await API.post(
      '/buyer_activity/join',
      { activity_id: currentActivity.value.id, products },
      { params: mallParam(), headers },
    )
    if (data.current && data.success) {
      ElMessage.success(data.msg || '加入成功')
      joinVisible.value = false
    } else {
      ElMessage.error(data.msg || '加入失败')
    }
  } catch {
    ElMessage.error('加入活动失败')
  } finally {
    joinSubmitting.value = false
  }
}

// ───── 退出对话框：加载已加入商品 ─────
function openLeaveDialog(activity: any) {
  currentActivity.value = activity
  leaveMode.value = 'all'
  joinedProducts.value = []
  leaveVisible.value = true
}

async function loadJoinedProducts() {
  if (!currentActivity.value) return
  leaveProductsLoading.value = true
  try {
    const { data } = await API.get('/buyer_activity/my_products', {
      params: {
        activity_id: currentActivity.value.id,
        page: 1,
        page_size: 50,
        ...mallParam(),
      },
      headers,
    })
    if (data.current) {
      // 只保留至少有一个规格已加入（或无规格但已加入）的商品
      const all: any[] = data.data || []
      joinedProducts.value = all
        .filter((p: any) => {
          if (p.specifications && p.specifications.length > 0) {
            return p.specifications.some((sp: any) => sp.already_joined)
          }
          return p.already_joined
        })
        .map((p: any) => ({ ...p, _leave: false }))
    }
  } catch {
    ElMessage.error('获取已加入商品失败')
  } finally {
    leaveProductsLoading.value = false
  }
}

async function submitLeave() {
  leaveSubmitting.value = true
  try {
    const body: any = { activity_id: currentActivity.value.id }
    if (leaveMode.value === 'partial') {
      const ids = joinedProducts.value.filter((p: any) => p._leave).map((p: any) => p.shopping_id)
      if (ids.length === 0) {
        ElMessage.warning('请至少选择一个要退出的商品')
        leaveSubmitting.value = false
        return
      }
      body.shopping_ids = ids
    }
    const { data } = await API.post('/buyer_activity/leave', body, { params: mallParam(), headers })
    if (data.current && data.success) {
      ElMessage.success(data.msg || '退出成功')
      leaveVisible.value = false
    } else {
      ElMessage.error(data.msg || '退出失败')
    }
  } catch {
    ElMessage.error('退出活动失败')
  } finally {
    leaveSubmitting.value = false
  }
}

onMounted(() => loadList(1))
</script>

<style scoped>
.join-activity { padding: 4px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.section-header h3 { margin: 0; font-size: 18px; font-weight: 600; }
.loading-box, .empty-box { padding: 60px 0; }
.pager { margin-top: 16px; display: flex; justify-content: flex-end; }

.activity-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(480px, 1fr)); gap: 16px; }
.activity-card { border-radius: 10px; transition: transform 0.2s; }
.activity-card:hover { transform: translateY(-2px); }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-header-right { display: flex; align-items: center; gap: 4px; }
.card-title-row { display: flex; align-items: center; gap: 8px; }
.card-name { font-size: 15px; font-weight: 600; }
.card-body { display: flex; flex-direction: column; gap: 12px; }
.card-info { display: flex; flex-direction: column; gap: 6px; }
.info-row { font-size: 13px; color: var(--el-text-color-regular); display: flex; }
.info-row .label { color: var(--el-text-color-secondary); min-width: 72px; flex-shrink: 0; }
.rules-text { color: var(--el-color-primary); font-weight: 500; }
.card-actions { display: flex; gap: 8px; margin-top: 4px; }

/* ── 商品选择列表 ── */
.product-list { max-height: 420px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; padding-right: 4px; }

.product-block { border: 1px solid var(--el-border-color-light); border-radius: 8px; overflow: hidden; }

.product-row,
.product-header-row,
.spec-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
}

.product-header-row { background: var(--el-fill-color-light); }

.spec-row { padding-left: 28px; border-top: 1px solid var(--el-border-color-lighter); }

.product-row.disabled,
.spec-row.disabled { opacity: 0.6; }

.prod-thumb { width: 44px; height: 44px; border-radius: 4px; flex-shrink: 0; }
.prod-thumb-placeholder { width: 44px; height: 44px; border-radius: 4px; background: var(--el-fill-color); flex-shrink: 0; }

.prod-name { flex: 1; font-size: 13px; line-height: 1.4; word-break: break-all; }
.spec-name { min-width: 80px; font-size: 13px; color: var(--el-text-color-regular); }
.spec-origin-price { font-size: 12px; color: var(--el-text-color-secondary); min-width: 72px; }

.price-input { width: 110px; }
.stock-input { width: 110px; }
.rule-price-hint {
  font-size: 12px;
  color: #cf1322;
  font-weight: 600;
  white-space: nowrap;
}
.rule-stacked-hint {
  font-size: 11px;
  color: var(--el-color-success);
  font-weight: 600;
  white-space: nowrap;
}
.rule-price-col {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.stackable-yes {
  color: var(--el-color-success);
  font-size: 13px;
  font-weight: 500;
}
.stackable-no {
  color: var(--el-text-color-placeholder);
  font-size: 13px;
}
.stacked-rate-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
  padding: 8px 12px;
  background: var(--el-color-success-light-9);
  border-radius: 6px;
  border: 1px solid var(--el-color-success-light-5);
}
.stacked-rate-label {
  font-size: 13px;
  color: var(--el-text-color-regular);
}
.stacked-rate-hint {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}
.stacked-coupon-tag {
  display: inline-block;
  font-size: 10px;
  color: var(--el-color-success-dark-2);
  background: var(--el-color-success-light-8);
  border-radius: 3px;
  padding: 0 4px;
  margin-left: 3px;
  white-space: nowrap;
}
.no-stack-hint {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  white-space: nowrap;
}

/* ── 退出商品列表 ── */
.leave-product-list { display: flex; flex-direction: column; gap: 8px; max-height: 320px; overflow-y: auto; }
.leave-product-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
}

@media (max-width: 768px) {
  .activity-cards { grid-template-columns: 1fr; }
  .product-row, .spec-row { flex-wrap: wrap; }
}
</style>
