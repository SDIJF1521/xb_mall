<template>
  <div class="activity-manage">
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">创建活动</el-button>
      <div class="toolbar-right">
        <el-select v-model="filterType" placeholder="活动类型" clearable style="width: 130px" @change="loadList(1)">
          <el-option label="秒杀" value="flash_sale" />
          <el-option label="满减" value="full_reduction" />
          <el-option label="折扣" value="discount" />
          <el-option label="拼团" value="group_buy" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px; margin-left: 8px" @change="loadList(1)">
          <el-option label="草稿" value="draft" />
          <el-option label="进行中" value="active" />
          <el-option label="已暂停" value="paused" />
          <el-option label="已结束" value="ended" />
        </el-select>
        <el-button :icon="Refresh" circle style="margin-left: 8px" @click="loadList(page)" />
      </div>
    </div>

    <div v-if="loading" class="loading-box"><el-skeleton :rows="5" animated /></div>
    <div v-else-if="list.length === 0" class="empty-box"><el-empty description="暂无活动" /></div>
    <div v-else>
      <el-table :data="list" stripe :header-cell-style="{ background: 'var(--el-fill-color-light)' }">
        <el-table-column prop="activity_no" label="编号" width="190" show-overflow-tooltip />
        <el-table-column prop="name" label="活动名称" min-width="150" show-overflow-tooltip />
        <el-table-column label="类型" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="actTypeTag(row.activity_type)">{{ actTypeLabel(row.activity_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="活动时间" width="180" align="center">
          <template #default="{ row }">
            <div style="font-size: 12px; line-height: 1.6">
              <div>{{ row.start_time?.slice(0, 16) }}</div>
              <div style="color: var(--el-text-color-placeholder)">至 {{ row.end_time?.slice(0, 16) }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTag(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" plain @click="showDetail(row.id)">详情</el-button>
            <el-button v-if="row.status === 'draft'" type="success" size="small" plain @click="updateStatus(row.id, 'active')">开始</el-button>
            <el-button v-if="row.status === 'active'" type="warning" size="small" plain @click="updateStatus(row.id, 'paused')">暂停</el-button>
            <el-button v-if="row.status === 'paused'" type="success" size="small" plain @click="updateStatus(row.id, 'active')">恢复</el-button>
            <el-button v-if="row.status === 'active'" type="info" size="small" plain @click="updateStatus(row.id, 'ended')">结束</el-button>
            <el-popconfirm v-if="row.status !== 'active'" title="确定删除？" @confirm="deleteActivity(row.id)">
              <template #reference>
                <el-button type="danger" size="small" plain>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <el-pagination :page-size="pageSize" layout="total, prev, pager, next" :total="total" :current-page="page" @current-change="loadList" />
      </div>
    </div>

    <!-- 创建对话框 -->
    <el-dialog v-model="createVisible" title="创建店铺活动" width="680px" destroy-on-close>
      <el-form :model="form" label-width="120px">
        <el-form-item label="活动名称" required>
          <el-input v-model="form.name" maxlength="200" placeholder="输入活动名称" />
        </el-form-item>
        <el-form-item label="活动类型" required>
          <el-radio-group v-model="form.activity_type" @change="onTypeChange">
            <el-radio value="flash_sale">秒杀</el-radio>
            <el-radio value="full_reduction">满减</el-radio>
            <el-radio value="discount">折扣</el-radio>
            <el-radio value="group_buy">拼团</el-radio>
          </el-radio-group>
        </el-form-item>

        <template v-if="form.activity_type === 'flash_sale'">
          <el-form-item label="折扣率">
            <el-input-number v-model="form.rules.discount_rate" :min="0.01" :max="0.99" :precision="2" style="width: 200px" />
            <span style="margin-left: 8px; color: var(--el-text-color-placeholder)">如 0.5 = 五折</span>
          </el-form-item>
        </template>

        <template v-if="form.activity_type === 'full_reduction'">
          <el-form-item label="满减梯度">
            <div v-for="(t, i) in form.rules.thresholds" :key="i" style="display: flex; gap: 8px; margin-bottom: 8px; align-items: center">
              <span>满</span>
              <el-input-number v-model="t.min_amount" :min="1" :precision="2" size="small" style="width: 120px" />
              <span>减</span>
              <el-input-number v-model="t.reduction" :min="1" :precision="2" size="small" style="width: 120px" />
              <el-button v-if="form.rules.thresholds.length > 1" type="danger" size="small" circle :icon="Minus" @click="form.rules.thresholds.splice(i, 1)" />
            </div>
            <el-button type="primary" size="small" plain :icon="Plus" @click="form.rules.thresholds.push({ min_amount: 100, reduction: 10 })">添加梯度</el-button>
          </el-form-item>
        </template>

        <template v-if="form.activity_type === 'discount'">
          <el-form-item label="折扣率">
            <el-input-number v-model="form.rules.discount_rate" :min="0.01" :max="0.99" :precision="2" style="width: 200px" />
            <span style="margin-left: 8px; color: var(--el-text-color-placeholder)">如 0.85 = 85折</span>
          </el-form-item>
        </template>

        <template v-if="form.activity_type === 'group_buy'">
          <el-form-item label="最少成团人数">
            <el-input-number v-model="form.rules.min_group_size" :min="2" style="width: 200px" />
          </el-form-item>
          <el-form-item label="折扣率">
            <el-input-number v-model="form.rules.discount_rate" :min="0.01" :max="0.99" :precision="2" style="width: 200px" />
          </el-form-item>
        </template>

        <!-- 折扣叠加设置：仅折扣率类活动（秒杀/折扣/拼团）显示 -->
        <template v-if="isPriceByRule">
          <el-form-item label="折扣叠加">
            <div class="stackable-row">
              <el-switch
                v-model="form.rules.stackable"
                active-text="支持叠加优惠券"
                inactive-text="不支持叠加"
              />
              <template v-if="form.rules.stackable">
                <el-icon v-if="couponsLoading" class="is-loading" style="margin-left:8px"><Loading /></el-icon>
                <span v-else-if="storeBestCoupon || productCouponMap.size" style="margin-left:8px; color:var(--el-color-success); font-size:12px">
                  <el-icon><CircleCheck /></el-icon> 已自动读取本店优惠券
                </span>
                <span v-else-if="!couponsLoading" style="margin-left:8px; color:var(--el-color-info); font-size:12px">
                  暂无可叠加优惠券
                </span>
              </template>
            </div>
            <div v-if="form.rules.stackable" class="stackable-desc">
              <el-icon style="color: var(--el-color-warning)"><InfoFilled /></el-icon>
              活动价可叠加优惠券，最终价 = 活动折后价 × 优惠券折扣率
            </div>
          </el-form-item>
        </template>

        <el-form-item label="活动商品">
          <div class="product-picker">
            <!-- 搜索栏 -->
            <div class="product-picker__search">
              <el-input
                v-model="productSearch"
                placeholder="搜索商品名称"
                clearable
                style="width: 240px"
                @keyup.enter="loadShopProducts()"
              />
              <el-button type="primary" size="default" @click="loadShopProducts()">搜索</el-button>
              <el-button size="default" @click="loadShopProducts(true)">全部</el-button>
            </div>

            <!-- 商品列表（带规格展开） -->
            <div v-if="productSearching" class="product-picker__loading">
              <el-skeleton :rows="2" animated />
            </div>
            <div v-else-if="productOptions.length" class="product-picker__list">
              <div v-for="p in productOptions" :key="p.shopping_id" class="product-picker__item-wrap">
                <!-- 商品行头 -->
                <div
                  class="product-picker__item"
                  :class="{ 'is-partially': isProductPartiallySelected(p), 'is-selected': isProductFullySelected(p) }"
                  @click="toggleExpandProduct(p)"
                >
                  <el-image
                    v-if="p.img"
                    :src="'data:image/png;base64,' + p.img"
                    fit="cover"
                    class="product-picker__img"
                  />
                  <div v-else class="product-picker__img product-picker__img--empty">
                    <el-icon><Goods /></el-icon>
                  </div>
                  <div class="product-picker__info">
                    <div class="product-picker__name">{{ p.name }}</div>
                    <div class="product-picker__id">
                      ID: {{ p.shopping_id }}
                      <span v-if="p.specifications?.length" class="spec-count">{{ p.specifications.length }} 个规格</span>
                    </div>
                  </div>
                  <div class="product-picker__actions">
                    <!-- 无规格商品：直接整体勾选 -->
                    <el-checkbox
                      v-if="!p.specifications?.length"
                      :model-value="isWholeProductSelected(p)"
                      @change="toggleWholeProduct(p)"
                      @click.stop
                    />
                    <!-- 有规格：展开箭头 -->
                    <el-icon v-else style="transition:transform 0.2s" :style="expandedProduct === p.shopping_id ? 'transform:rotate(90deg)' : ''">
                      <ArrowRight />
                    </el-icon>
                  </div>
                </div>

                <!-- 规格展开列表 -->
                <div v-if="p.specifications?.length && expandedProduct === p.shopping_id" class="product-picker__specs">
                  <div
                    v-for="sp in p.specifications"
                    :key="sp.specification_id"
                    class="product-picker__spec-row"
                    @click="toggleSpec(p, sp)"
                  >
                    <el-checkbox
                      :model-value="isSpecSelected(p.shopping_id, sp.specification_id)"
                      @change="toggleSpec(p, sp)"
                      @click.stop
                    />
                    <span class="spec-name">{{ sp.name }}</span>
                    <span class="spec-price">¥{{ sp.price }}</span>
                    <span class="spec-stock">库存 {{ sp.stock }}</span>
                  </div>
                  <div class="product-picker__spec-actions">
                    <el-link type="primary" size="small" @click.stop="selectAllSpecs(p)">全选</el-link>
                    <el-link size="small" @click.stop="deselectAllSpecs(p)" style="margin-left: 8px">清除</el-link>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="productSearched" class="product-picker__empty">
              <el-empty description="未找到商品" :image-size="60" />
            </div>

            <!-- 已选规格区 -->
            <div v-if="activityProducts.length" class="product-picker__selected">
              <div class="product-picker__selected-title">
                已选 {{ activityProducts.length }} 条规格
                <template v-if="isPriceByRule">
                  — 按 {{ discountRateDisplay }} 折计算
                  <el-tag v-if="form.rules.stackable" size="small" type="warning" style="margin-left: 4px">支持叠加优惠券</el-tag>
                  <el-tag v-else size="small" type="info" style="margin-left: 4px">不叠加</el-tag>
                </template>
                <template v-else-if="isCartLevel"> — 满减为购物车优惠，无需设置活动价</template>
                <template v-else> — 请为每条规格设置活动价和库存</template>
              </div>

              <el-alert v-if="isPriceByRule && !form.rules.stackable"
                :title="`价格将按折扣率 ${discountRateDisplay} 折自动计算，不可叠加优惠券，只需设置活动库存（选填）`"
                type="warning" :closable="false" show-icon style="margin-bottom: 8px"
              />
              <el-alert v-else-if="isPriceByRule && form.rules.stackable"
                :title="`活动价按 ${discountRateDisplay} 折计算，支持叠加优惠券`"
                type="success" :closable="false" show-icon style="margin-bottom: 8px"
              />
              <el-alert v-else-if="isCartLevel"
                title="满减为购物车级优惠，商品本身价格不变"
                type="info" :closable="false" show-icon style="margin-bottom: 8px"
              />

              <div v-for="(sp, i) in activityProducts" :key="`${sp.shopping_id}-${sp.specification_id}`" class="activity-product-row">
                <div class="activity-product-label">
                  <el-tag size="small" closable @close="activityProducts.splice(i, 1)">
                    {{ sp.product_name }}
                  </el-tag>
                  <span v-if="sp.spec_name" class="activity-spec-name">/ {{ sp.spec_name }}</span>
                  <span class="activity-origin-price">原价 ¥{{ sp.origin_price }}</span>
                  <el-tag v-if="getExistingActivityInfo(sp.shopping_id)" size="small" type="warning" style="margin-left: 4px">
                    {{ getExistingActivityInfo(sp.shopping_id) }}
                  </el-tag>
                </div>
                <div v-if="!isPriceByRule && !isCartLevel" class="activity-product-fields">
                  <el-input-number
                    v-model="sp.activity_price"
                    :min="0.01" :max="sp.origin_price" :precision="2"
                    placeholder="活动价"
                    size="small" style="width: 120px"
                  />
                  <el-input-number v-model="sp.activity_stock" :min="1" placeholder="库存" size="small" style="width: 100px" />
                </div>
                <div v-else-if="isPriceByRule" class="activity-product-fields">
                  <div class="price-stack-col">
                    <!-- 叠加开启且加载中 -->
                    <template v-if="form.rules.stackable && couponsLoading">
                      <span class="calc-price">
                        活动价 ≈ ¥{{ calcActivityPrice(sp.origin_price, sp.shopping_id) }}
                      </span>
                      <el-icon class="is-loading" style="font-size:12px;margin-left:4px"><Loading /></el-icon>
                    </template>
                    <!-- 叠加开启且检测到优惠券：主估算直接显示折上折金额 -->
                    <template v-else-if="form.rules.stackable && calcStackedPrice(sp.origin_price, sp.shopping_id)">
                      <span class="calc-price" style="text-decoration:line-through; color:var(--el-color-info); font-size:12px">
                        活动价 ¥{{ calcActivityPrice(sp.origin_price, sp.shopping_id) }}
                      </span>
                      <span class="stacked-price" style="font-weight:600; color:var(--el-color-danger)">
                        折上折 ≈ ¥{{ calcStackedPrice(sp.origin_price, sp.shopping_id) }}
                        <span class="stacked-hint">（{{ getStackedInfo(sp.shopping_id)?.name }}）</span>
                      </span>
                    </template>
                    <!-- 叠加开启但无可用券，或未开启叠加：仅展示活动价 -->
                    <template v-else>
                      <span class="calc-price">
                        活动价 ≈ ¥{{ calcActivityPrice(sp.origin_price, sp.shopping_id) }}
                      </span>
                      <span v-if="form.rules.stackable" class="stacked-price" style="color:var(--el-color-info)">
                        无可叠加优惠券
                      </span>
                    </template>
                  </div>
                  <el-input-number v-model="sp.activity_stock" :min="1" placeholder="库存限制(选填)" size="small" style="width: 130px" />
                </div>
              </div>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="活动时间" required>
          <el-date-picker v-model="form.timeRange" type="datetimerange" range-separator="至" start-placeholder="开始时间" end-placeholder="结束时间" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="活动说明">
          <el-input v-model="form.description" type="textarea" :rows="3" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="活动详情" width="700px">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="编号" :span="2">{{ detail.activity_no }}</el-descriptions-item>
          <el-descriptions-item label="名称" :span="2">{{ detail.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ actTypeLabel(detail.activity_type) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTag(detail.status)" size="small">{{ statusLabel(detail.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="活动时间" :span="2">{{ detail.start_time?.slice(0, 16) }} 至 {{ detail.end_time?.slice(0, 16) }}</el-descriptions-item>
          <el-descriptions-item label="规则" :span="2">
            <pre style="margin: 0; white-space: pre-wrap; font-size: 13px">{{ JSON.stringify(detail.rules, null, 2) }}</pre>
          </el-descriptions-item>
          <el-descriptions-item v-if="detail.description" label="说明" :span="2">{{ detail.description }}</el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">{{ detail.created_at?.slice(0, 16) }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="detail.products?.length" style="margin-top: 20px">
          <h4 style="margin-bottom: 10px">活动商品 ({{ detail.products.length }})</h4>
          <el-table :data="detail.products" size="small" stripe>
            <el-table-column prop="shopping_id" label="商品ID" width="90" />
            <el-table-column label="规格ID" width="90">
              <template #default="{ row }">{{ row.specification_id ?? '全部' }}</template>
            </el-table-column>
            <el-table-column label="活动价" width="130">
              <template #default="{ row }">
                <template v-if="['flash_sale','discount','group_buy'].includes(detail.activity_type)">
                  <el-tag size="small" type="warning">按折扣率计算</el-tag>
                </template>
                <template v-else-if="detail.activity_type === 'full_reduction'">
                  <el-tag size="small" type="info">满减（购物车）</el-tag>
                </template>
                <template v-else>{{ row.activity_price ? `¥${row.activity_price}` : '-' }}</template>
              </template>
            </el-table-column>
            <el-table-column label="活动库存" width="100">
              <template #default="{ row }">{{ row.activity_stock ?? '不限' }}</template>
            </el-table-column>
            <el-table-column prop="sold_count" label="已售" width="80" />
          </el-table>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Plus, Refresh, Minus, Goods, CircleCheckFilled, ArrowRight, InfoFilled, Loading, CircleCheck } from '@element-plus/icons-vue'

defineOptions({ name: 'BuyerActivityManage' })

const props = defineProps<{ mallId?: number | null }>()

const API = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const token = localStorage.getItem('buyer_access_token') || ''
const headers = { 'access-token': token }

function mallParam(): Record<string, any> {
  return props.mallId ? { mall_id: props.mallId } : {}
}

const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const filterType = ref('')
const filterStatus = ref('')

const createVisible = ref(false)
const submitting = ref(false)

function defaultRules(type: string) {
  if (type === 'flash_sale') return { discount_rate: 0.5, stackable: false }
  if (type === 'full_reduction') return { thresholds: [{ min_amount: 100, reduction: 10 }] }
  if (type === 'discount') return { discount_rate: 0.85, stackable: false }
  if (type === 'group_buy') return { min_group_size: 2, discount_rate: 0.8, stackable: false }
  return {}
}

const form = ref<any>({
  name: '', activity_type: 'flash_sale',
  rules: defaultRules('flash_sale'),
  timeRange: null, description: '',
})

interface SelectedSpec {
  mall_id: number
  shopping_id: number
  product_name: string
  specification_id: number | null
  spec_name: string
  origin_price: number
  activity_price: number | null
  activity_stock: number | null
}

const productSearch = ref('')
const productOptions = ref<any[]>([])
const productSearching = ref(false)
const productSearched = ref(false)
const expandedProduct = ref<number | null>(null)
const activityProducts = ref<SelectedSpec[]>([])

// ── 已有活动折扣：通过后端路由一次性获取本店商品参与的生效折扣活动 ──

interface ExistingActivityRate {
  combinedRate: number
  activityNames: string[]
}

const existingRateMap = ref<Map<number, ExistingActivityRate>>(new Map())

async function loadExistingActivities() {
  if (!props.mallId) return
  existingRateMap.value = new Map()
  try {
    const { data } = await API.get('/buyer_activity/product_discounts', {
      params: mallParam(),
      headers,
    })
    if (!data.current || !data.data) return

    const newMap = new Map<number, ExistingActivityRate>()
    for (const [sid, activities] of Object.entries(data.data as Record<string, any[]>)) {
      const shoppingId = Number(sid)
      let combinedRate = 1
      const names: string[] = []
      for (const act of activities) {
        const dr = Number(act.discount_rate)
        if (dr > 0 && dr < 1) {
          combinedRate *= dr
          names.push(act.activity_name)
        }
      }
      if (names.length) {
        newMap.set(shoppingId, { combinedRate, activityNames: names })
      }
    }
    existingRateMap.value = newMap
  } catch { /* 静默失败 */ }
}

function getExistingRate(shoppingId: number): number {
  return existingRateMap.value.get(shoppingId)?.combinedRate ?? 1
}

function getExistingActivityInfo(shoppingId: number): string {
  const info = existingRateMap.value.get(shoppingId)
  if (!info) return ''
  return `已有${info.activityNames.length}个折扣（${(info.combinedRate * 10).toFixed(1)}折）`
}

/** 计算考虑了已有活动折扣后的活动价 = 原价 × 已有折扣率 × 新折扣率 */
function calcActivityPrice(originPrice: number, shoppingId: number): string {
  const dr = form.value.rules?.discount_rate
  if (dr == null || !originPrice) return '0.00'
  const existing = getExistingRate(shoppingId)
  return (originPrice * existing * dr).toFixed(2)
}

// ── 折上折：自动读取本店优惠券 ──

interface CouponStackInfo {
  rate: number   // discount_value，如 0.9 表示九折
  name: string
}

const storeBestCoupon = ref<CouponStackInfo | null>(null)
const productCouponMap = ref<Map<number, CouponStackInfo>>(new Map())
const couponsLoading = ref(false)

/** 拉取本店 active 的 discount 类型优惠券，构建商品 → 最优折扣映射 */
async function loadStoreCoupons() {
  if (!props.mallId) return
  couponsLoading.value = true
  storeBestCoupon.value = null
  productCouponMap.value = new Map()
  try {
    const { data } = await API.get('/buyer_coupon/list', {
      params: { status: 'active', page: 1, page_size: 100, ...mallParam() },
      headers,
    })
    if (!data.current) return

    const discountCoupons: any[] = (data.list || []).filter(
      (c: any) => c.coupon_type === 'discount' && c.discount_value > 0 && c.discount_value < 1,
    )

    // 店铺通用券（scope=all_mall 或 store）取最优（折扣率最小）
    const storeWide = discountCoupons.filter(
      (c: any) => c.scope === 'all_mall' || c.scope === 'store',
    )
    const bestSW = storeWide.reduce<any>(
      (best, c) => (!best || c.discount_value < best.discount_value) ? c : best,
      null,
    )
    if (bestSW) storeBestCoupon.value = { rate: bestSW.discount_value, name: bestSW.name }

    // 商品专属券并发拉详情，按 shopping_id 建最优券映射
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
    // 静默失败，仅影响估算展示
  } finally {
    couponsLoading.value = false
  }
}

/** 获取某商品最佳可叠加优惠券（专属 > 通用，折扣更大优先） */
function getStackedInfo(shoppingId: number): CouponStackInfo | null {
  const productSpecific = productCouponMap.value.get(shoppingId)
  const storeWide = storeBestCoupon.value
  if (!productSpecific && !storeWide) return null
  if (!productSpecific) return storeWide
  if (!storeWide) return productSpecific
  return productSpecific.rate <= storeWide.rate ? productSpecific : storeWide
}

/** 计算折上折价 = 原价 × 已有活动折扣率 × 新活动折扣率 × 优惠券折扣率 */
function calcStackedPrice(originPrice: number, shoppingId: number): string {
  const info = getStackedInfo(shoppingId)
  if (!info || !originPrice) return ''
  const dr = form.value.rules?.discount_rate
  if (dr == null) return ''
  const existing = getExistingRate(shoppingId)
  return (originPrice * existing * dr * info.rate).toFixed(2)
}

// 开启叠加时自动加载优惠券
watch(
  () => form.value.rules?.stackable,
  (val) => { if (val) loadStoreCoupons() },
)

async function loadShopProducts(clear?: boolean) {
  if (!props.mallId) return ElMessage.warning('未选择店铺')
  if (clear) productSearch.value = ''
  productSearching.value = true
  productSearched.value = false
  try {
    const params: Record<string, any> = { page: 1, page_size: 50, ...mallParam() }
    if (productSearch.value.trim()) params.search = productSearch.value.trim()
    const { data } = await API.get('/buyer_activity/shop_products', { params, headers })
    if (data.current && data.data) {
      productOptions.value = data.data
    } else {
      productOptions.value = []
    }
  } catch {
    ElMessage.error('搜索商品失败')
    productOptions.value = []
  } finally {
    productSearching.value = false
    productSearched.value = true
  }
}

// ── 整体商品（无规格）选择 ──
function isWholeProductSelected(p: any) {
  return activityProducts.value.some(s => s.shopping_id === p.shopping_id && s.specification_id === null)
}
function toggleWholeProduct(p: any) {
  if (isWholeProductSelected(p)) {
    activityProducts.value = activityProducts.value.filter(s => s.shopping_id !== p.shopping_id)
  } else {
    activityProducts.value = activityProducts.value.filter(s => s.shopping_id !== p.shopping_id)
    activityProducts.value.push({
      mall_id: props.mallId!,
      shopping_id: p.shopping_id,
      product_name: p.name,
      specification_id: null,
      spec_name: '',
      origin_price: p.specifications?.[0]?.price ?? 0,
      activity_price: null,
      activity_stock: null,
    })
  }
}

// ── 规格选择 ──
function isSpecSelected(shopping_id: number, spec_id: number) {
  return activityProducts.value.some(s => s.shopping_id === shopping_id && s.specification_id === spec_id)
}
function toggleSpec(p: any, sp: any) {
  if (isSpecSelected(p.shopping_id, sp.specification_id)) {
    activityProducts.value = activityProducts.value.filter(
      s => !(s.shopping_id === p.shopping_id && s.specification_id === sp.specification_id)
    )
  } else {
    activityProducts.value.push({
      mall_id: props.mallId!,
      shopping_id: p.shopping_id,
      product_name: p.name,
      specification_id: sp.specification_id,
      spec_name: sp.name,
      origin_price: sp.price,
      activity_price: null,
      activity_stock: null,
    })
  }
}
function selectAllSpecs(p: any) {
  for (const sp of p.specifications || []) {
    if (!isSpecSelected(p.shopping_id, sp.specification_id)) {
      activityProducts.value.push({
        mall_id: props.mallId!,
        shopping_id: p.shopping_id,
        product_name: p.name,
        specification_id: sp.specification_id,
        spec_name: sp.name,
        origin_price: sp.price,
        activity_price: null,
        activity_stock: null,
      })
    }
  }
}
function deselectAllSpecs(p: any) {
  activityProducts.value = activityProducts.value.filter(s => s.shopping_id !== p.shopping_id)
}
function isProductPartiallySelected(p: any) {
  if (!p.specifications?.length) return false
  const selected = p.specifications.filter((sp: any) => isSpecSelected(p.shopping_id, sp.specification_id))
  return selected.length > 0 && selected.length < p.specifications.length
}
function isProductFullySelected(p: any) {
  if (!p.specifications?.length) return isWholeProductSelected(p)
  return p.specifications.every((sp: any) => isSpecSelected(p.shopping_id, sp.specification_id))
}
function toggleExpandProduct(p: any) {
  if (!p.specifications?.length) return  // 无规格，点击直接切换整体选中
  expandedProduct.value = expandedProduct.value === p.shopping_id ? null : p.shopping_id
}

const detailVisible = ref(false)
const detail = ref<any>(null)

function actTypeLabel(t: string) {
  return { flash_sale: '秒杀', full_reduction: '满减', discount: '折扣', group_buy: '拼团' }[t] || t
}
function actTypeTag(t: string) {
  return { flash_sale: 'danger', full_reduction: 'warning', discount: 'success', group_buy: '' }[t] || 'info'
}
function statusLabel(s: string) {
  return { draft: '草稿', active: '进行中', paused: '已暂停', ended: '已结束' }[s] || s
}
function statusTag(s: string) {
  return { draft: 'info', active: 'success', paused: 'warning', ended: 'danger' }[s] || 'info'
}

/** 价格由 discount_rate 规则决定，商家不得手动设置 activity_price */
const isPriceByRule = computed(() =>
  ['flash_sale', 'discount', 'group_buy'].includes(form.value.activity_type)
)
/** 满减为购物车级，商品单价不变 */
const isCartLevel = computed(() => form.value.activity_type === 'full_reduction')

/** 当前折扣率的折扣显示（如 0.8 → "8.0"） */
const discountRateDisplay = computed(() => {
  const dr = form.value.rules?.discount_rate
  return dr != null ? (dr * 10).toFixed(1) : '-'
})

function onTypeChange(type: string) {
  form.value.rules = defaultRules(type)
}

async function loadList(p: number) {
  loading.value = true
  page.value = p
  try {
    const params: Record<string, any> = { page: p, page_size: pageSize.value, ...mallParam() }
    if (filterType.value) params.activity_type = filterType.value
    if (filterStatus.value) params.status = filterStatus.value
    const { data } = await API.get('/buyer_activity/list', { params, headers })
    if (data.current) {
      list.value = data.list
      total.value = data.total
    } else {
      ElMessage.warning(data.msg)
    }
  } catch {
    ElMessage.error('获取活动列表失败')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  form.value = {
    name: '', activity_type: 'flash_sale',
    rules: defaultRules('flash_sale'),
    timeRange: null, description: '',
  }
  activityProducts.value = []
  productOptions.value = []
  productSearched.value = false
  productSearch.value = ''
  expandedProduct.value = null
  createVisible.value = true
  loadShopProducts(true)
  loadExistingActivities()
}

async function submitCreate() {
  const f = form.value
  if (!f.name?.trim()) return ElMessage.warning('请输入活动名称')
  if (!f.timeRange || f.timeRange.length < 2) return ElMessage.warning('请选择活动时间')

  submitting.value = true
  try {
    const body: Record<string, any> = {
      name: f.name, activity_type: f.activity_type,
      start_time: f.timeRange[0], end_time: f.timeRange[1],
      rules: f.rules, platform_scope: 'all',
      description: f.description,
    }
    if (activityProducts.value.length) {
      body.products = activityProducts.value.map(p => ({
        mall_id: p.mall_id,
        shopping_id: p.shopping_id,
        specification_id: p.specification_id ?? undefined,
        activity_price: p.activity_price,
        activity_stock: p.activity_stock,
      }))
    }
    const { data } = await API.post('/buyer_activity/create', body, { params: mallParam(), headers })
    if (data.success) {
      ElMessage.success('创建成功')
      createVisible.value = false
      loadList(1)
    } else {
      ElMessage.error(data.msg)
    }
  } catch {
    ElMessage.error('创建失败')
  } finally {
    submitting.value = false
  }
}

async function updateStatus(id: number, status: string) {
  try {
    const { data } = await API.post('/buyer_activity/status', { activity_id: id, status }, { params: mallParam(), headers })
    if (data.success) {
      ElMessage.success(data.msg)
      loadList(page.value)
    } else {
      ElMessage.error(data.msg)
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

async function deleteActivity(id: number) {
  try {
    const { data } = await API.post('/buyer_activity/delete', { activity_id: id }, { params: mallParam(), headers })
    if (data.success) {
      ElMessage.success('已删除')
      loadList(page.value)
    } else {
      ElMessage.error(data.msg)
    }
  } catch {
    ElMessage.error('删除失败')
  }
}

async function showDetail(id: number) {
  try {
    const { data } = await API.get('/buyer_activity/detail', { params: { activity_id: id, ...mallParam() }, headers })
    if (data.success) {
      detail.value = data.data
      detailVisible.value = true
    } else {
      ElMessage.error(data.msg)
    }
  } catch {
    ElMessage.error('获取详情失败')
  }
}

onMounted(() => loadList(1))
</script>

<style scoped>
.activity-manage { padding: 4px; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px; }
.toolbar-right { display: flex; align-items: center; }
.loading-box, .empty-box { padding: 60px 0; }
.pager { margin-top: 16px; display: flex; justify-content: flex-end; }

.product-picker { width: 100%; }
.product-picker__search { display: flex; gap: 8px; margin-bottom: 12px; }
.product-picker__loading { padding: 16px 0; }
.product-picker__list {
  max-height: 220px;
  overflow-y: auto;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 6px;
}
.product-picker__item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}
.product-picker__item:hover { background: var(--el-fill-color-light); }
.product-picker__item.is-selected { background: var(--el-color-primary-light-9); }
.product-picker__img {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  flex-shrink: 0;
  overflow: hidden;
}
.product-picker__img--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color);
  color: var(--el-text-color-placeholder);
  font-size: 20px;
}
.product-picker__info { flex: 1; min-width: 0; }
.product-picker__name {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.product-picker__id { font-size: 11px; color: var(--el-text-color-placeholder); }
.product-picker__check { color: var(--el-color-primary); font-size: 18px; }
.product-picker__empty { padding: 12px 0; }
.product-picker__actions { display: flex; align-items: center; gap: 6px; margin-left: auto; flex-shrink: 0; }
.product-picker__item-wrap { margin-bottom: 2px; border-radius: 6px; overflow: hidden; }
.product-picker__item.is-partially { background: var(--el-color-warning-light-9); }
.spec-count { font-size: 10px; color: var(--el-color-primary); margin-left: 4px; }

.product-picker__specs {
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
  border-top: none;
  border-radius: 0 0 6px 6px;
  padding: 6px 8px 4px 44px;
}
.product-picker__spec-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 0;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.12s;
  &:hover { background: var(--el-fill-color); }
}
.spec-name { font-size: 13px; flex: 1; }
.spec-price { font-size: 12px; color: var(--el-color-danger); font-weight: 500; }
.spec-stock { font-size: 11px; color: var(--el-text-color-placeholder); }
.product-picker__spec-actions { display: flex; padding: 4px 0 2px; border-top: 1px dashed var(--el-border-color-lighter); margin-top: 4px; }

.product-picker__selected {
  margin-top: 12px;
  padding: 12px;
  background: var(--el-bg-color-page);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
}
.product-picker__selected-title {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 10px;
  font-weight: 500;
  line-height: 1.6;
}
.activity-product-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  background: var(--el-fill-color);
  transition: background 0.15s;
}
.activity-product-row:hover { background: var(--el-fill-color-light); }
.activity-product-label {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
  row-gap: 4px;
}
.activity-spec-name {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}
.activity-origin-price {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  white-space: nowrap;
}
.calc-price {
  font-size: 13px;
  color: var(--el-color-danger);
  font-weight: 600;
  white-space: nowrap;
}
.stacked-price {
  font-size: 12px;
  color: var(--el-color-success);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 2px;
  white-space: nowrap;
}
.stacked-hint {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  font-weight: normal;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.price-stack-col {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 180px;
  flex-shrink: 0;
}
.activity-product-fields {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-shrink: 0;
}
.stackable-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.stackable-hint-text {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.stackable-hint-sub {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}
.stackable-desc {
  margin-top: 6px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
