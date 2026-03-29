<template>
  <div class="coupon-manage">
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">创建优惠券</el-button>
      <div class="toolbar-right">
        <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 130px" @change="loadList(1)">
          <el-option label="草稿" value="draft" />
          <el-option label="已上线" value="active" />
          <el-option label="已暂停" value="paused" />
          <el-option label="已过期" value="expired" />
        </el-select>
        <el-button :icon="Refresh" circle style="margin-left: 8px" @click="loadList(page)" />
      </div>
    </div>

    <div v-if="loading" class="loading-box"><el-skeleton :rows="5" animated /></div>
    <div v-else-if="list.length === 0" class="empty-box"><el-empty description="暂无优惠券" /></div>
    <div v-else>
      <el-table :data="list" stripe :header-cell-style="{ background: 'var(--el-fill-color-light)' }">
        <el-table-column prop="coupon_no" label="编号" width="190" show-overflow-tooltip />
        <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
        <el-table-column label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="typeTag(row.coupon_type)">{{ typeLabel(row.coupon_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="优惠" width="140" align="center">
          <template #default="{ row }">
            <span v-if="row.coupon_type === 'full_reduction'">满{{ row.min_order_amount }}减{{ row.discount_value }}</span>
            <span v-else-if="row.coupon_type === 'discount'">{{ (row.discount_value * 10).toFixed(1) }}折</span>
            <span v-else>减{{ row.discount_value }}元</span>
          </template>
        </el-table-column>
        <el-table-column label="领取/总量" width="110" align="center">
          <template #default="{ row }">
            {{ row.claimed_count }} / {{ row.total_count || '不限' }}
          </template>
        </el-table-column>
        <el-table-column label="有效期" width="180" align="center">
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
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" plain @click="showDetail(row.id)">详情</el-button>
            <el-button v-if="row.status === 'draft'" type="success" size="small" plain @click="updateStatus(row.id, 'active')">上线</el-button>
            <el-button v-if="row.status === 'active'" type="warning" size="small" plain @click="updateStatus(row.id, 'paused')">暂停</el-button>
            <el-button v-if="row.status === 'paused'" type="success" size="small" plain @click="updateStatus(row.id, 'active')">恢复</el-button>
            <el-popconfirm v-if="row.status !== 'active'" title="确定删除？" @confirm="deleteCoupon(row.id)">
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
    <el-dialog v-model="createVisible" title="创建店铺优惠券" width="640px" destroy-on-close>
      <el-form :model="form" label-width="120px">
        <el-form-item label="优惠券名称" required>
          <el-input v-model="form.name" maxlength="200" placeholder="输入优惠券名称" />
        </el-form-item>
        <el-form-item label="优惠券类型" required>
          <el-radio-group v-model="form.coupon_type">
            <el-radio value="full_reduction">满减</el-radio>
            <el-radio value="discount">折扣</el-radio>
            <el-radio value="fixed_amount">固定金额</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="最低订单金额" required>
          <el-input-number v-model="form.min_order_amount" :min="0" :precision="2" style="width: 200px" />
          <span style="margin-left: 8px; color: var(--el-text-color-placeholder)">元</span>
        </el-form-item>
        <el-form-item label="优惠值" required>
          <el-input-number v-model="form.discount_value" :min="0.01" :precision="2" style="width: 200px" />
          <span style="margin-left: 8px; color: var(--el-text-color-placeholder)">
            {{ form.coupon_type === 'discount' ? '（如0.85表示85折）' : '元' }}
          </span>
        </el-form-item>
        <el-form-item v-if="form.coupon_type === 'discount'" label="最大优惠">
          <el-input-number v-model="form.max_discount" :min="0" :precision="2" style="width: 200px" />
          <span style="margin-left: 8px; color: var(--el-text-color-placeholder)">元（封顶金额）</span>
        </el-form-item>
        <el-form-item label="发放总量">
          <el-input-number v-model="form.total_count" :min="0" style="width: 200px" />
          <span style="margin-left: 8px; color: var(--el-text-color-placeholder)">0 = 不限量</span>
        </el-form-item>
        <el-form-item label="每人限领">
          <el-input-number v-model="form.per_user_limit" :min="1" style="width: 200px" />
        </el-form-item>
        <el-form-item label="适用范围">
          <el-radio-group v-model="form.scope" @change="onScopeChange">
            <el-radio value="store">本店通用</el-radio>
            <el-radio value="product">指定商品</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.scope === 'product'" label="选择商品" required>
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
                <!-- 商品行 -->
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
                    <!-- 无规格：直接勾选整个商品 -->
                    <el-checkbox
                      v-if="!p.specifications?.length"
                      :model-value="isWholeProductSelected(p)"
                      @change="toggleWholeProduct(p)"
                      @click.stop
                    />
                    <!-- 有规格：展开箭头 -->
                    <el-icon v-else :style="expandedProduct === p.shopping_id ? 'transform:rotate(90deg)' : ''" style="transition:transform 0.2s">
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
                    <el-link type="primary" size="small" @click.stop="selectAllSpecs(p)">全选规格</el-link>
                    <el-link size="small" @click.stop="deselectAllSpecs(p)" style="margin-left: 8px">清除</el-link>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="productSearched" class="product-picker__empty">
              <el-empty description="未找到商品" :image-size="60" />
            </div>

            <!-- 已选规格区 -->
            <div v-if="selectedProducts.length" class="product-picker__selected">
              <div class="product-picker__selected-title">
                已选 {{ selectedProducts.length }} 条（规格/商品）
              </div>
              <div class="selected-tags">
                <div
                  v-for="(sp, i) in selectedProducts"
                  :key="`${sp.shopping_id}-${sp.specification_id}`"
                  class="selected-tag-item"
                >
                  <el-tag
                    closable
                    :type="sp.specification_id ? 'success' : ''"
                    @close="selectedProducts.splice(i, 1)"
                  >
                    {{ sp.product_name }}
                    <span v-if="sp.spec_name"> · {{ sp.spec_name }}</span>
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="有效期" required>
          <el-date-picker v-model="form.timeRange" type="datetimerange" range-separator="至" start-placeholder="开始时间" end-placeholder="结束时间" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="使用说明">
          <el-input v-model="form.description" type="textarea" :rows="3" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="优惠券详情" width="600px">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="编号" :span="2">{{ detail.coupon_no }}</el-descriptions-item>
          <el-descriptions-item label="名称" :span="2">{{ detail.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ typeLabel(detail.coupon_type) }}</el-descriptions-item>
          <el-descriptions-item label="适用范围">{{ detail.scope === 'store' ? '本店通用' : detail.scope === 'product' ? '指定商品' : '全商城' }}</el-descriptions-item>
          <el-descriptions-item label="最低金额">¥{{ detail.min_order_amount }}</el-descriptions-item>
          <el-descriptions-item label="优惠值">
            <span v-if="detail.coupon_type === 'discount'">{{ (detail.discount_value * 10).toFixed(1) }}折</span>
            <span v-else>¥{{ detail.discount_value }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="领取/使用/总量">{{ detail.claimed_count }} / {{ detail.used_count }} / {{ detail.total_count || '不限' }}</el-descriptions-item>
          <el-descriptions-item label="每人限领">{{ detail.per_user_limit }}张</el-descriptions-item>
          <el-descriptions-item label="有效期" :span="2">{{ detail.start_time?.slice(0, 16) }} 至 {{ detail.end_time?.slice(0, 16) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTag(detail.status)" size="small">{{ statusLabel(detail.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ detail.created_at?.slice(0, 16) }}</el-descriptions-item>
          <el-descriptions-item v-if="detail.description" label="说明" :span="2">{{ detail.description }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="detail.products?.length" style="margin-top: 16px">
          <h4 style="margin-bottom: 8px">适用商品 ({{ detail.products.length }})</h4>
          <el-table :data="detail.products" size="small" stripe>
            <el-table-column prop="shopping_id" label="商品ID" width="100" />
            <el-table-column label="规格" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.specification_id" size="small" type="success">规格 {{ row.specification_id }}</el-tag>
                <span v-else style="color: var(--el-text-color-placeholder); font-size: 12px">全部规格</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Plus, Refresh, Goods, CircleCheckFilled, ArrowRight } from '@element-plus/icons-vue'

defineOptions({ name: 'BuyerCouponManage' })

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
const filterStatus = ref('')

const createVisible = ref(false)
const submitting = ref(false)
const form = ref<any>({
  name: '', coupon_type: 'full_reduction', min_order_amount: 0,
  discount_value: 10, max_discount: null, total_count: 0,
  per_user_limit: 1, scope: 'store',
  timeRange: null, description: '',
})

interface SelectedItem {
  mall_id: number
  shopping_id: number
  product_name: string
  specification_id: number | null
  spec_name: string
}

const productSearch = ref('')
const productOptions = ref<any[]>([])
const productSearching = ref(false)
const productSearched = ref(false)
const expandedProduct = ref<number | null>(null)
const selectedProducts = ref<SelectedItem[]>([])

function onScopeChange() {
  if (form.value.scope === 'product') {
    selectedProducts.value = []
    productOptions.value = []
    productSearched.value = false
    expandedProduct.value = null
    loadShopProducts(true)
  }
}

async function loadShopProducts(clear?: boolean) {
  if (!props.mallId) return ElMessage.warning('未选择店铺')
  if (clear) productSearch.value = ''
  productSearching.value = true
  productSearched.value = false
  try {
    const params: Record<string, any> = { page: 1, page_size: 50, ...mallParam() }
    if (productSearch.value.trim()) params.search = productSearch.value.trim()
    const { data } = await API.get('/buyer_activity/shop_products', { params, headers })
    productOptions.value = data.current ? (data.data || []) : []
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
  return selectedProducts.value.some(s => s.shopping_id === p.shopping_id && s.specification_id === null)
}
function toggleWholeProduct(p: any) {
  if (isWholeProductSelected(p)) {
    selectedProducts.value = selectedProducts.value.filter(s => s.shopping_id !== p.shopping_id)
  } else {
    selectedProducts.value = selectedProducts.value.filter(s => s.shopping_id !== p.shopping_id)
    selectedProducts.value.push({
      mall_id: props.mallId!, shopping_id: p.shopping_id,
      product_name: p.name, specification_id: null, spec_name: '',
    })
  }
}

// ── 规格选择 ──
function isSpecSelected(shopping_id: number, spec_id: number) {
  return selectedProducts.value.some(s => s.shopping_id === shopping_id && s.specification_id === spec_id)
}
function toggleSpec(p: any, sp: any) {
  if (isSpecSelected(p.shopping_id, sp.specification_id)) {
    selectedProducts.value = selectedProducts.value.filter(
      s => !(s.shopping_id === p.shopping_id && s.specification_id === sp.specification_id)
    )
  } else {
    selectedProducts.value.push({
      mall_id: props.mallId!, shopping_id: p.shopping_id,
      product_name: p.name, specification_id: sp.specification_id, spec_name: sp.name,
    })
  }
}
function selectAllSpecs(p: any) {
  for (const sp of p.specifications || []) {
    if (!isSpecSelected(p.shopping_id, sp.specification_id)) {
      selectedProducts.value.push({
        mall_id: props.mallId!, shopping_id: p.shopping_id,
        product_name: p.name, specification_id: sp.specification_id, spec_name: sp.name,
      })
    }
  }
}
function deselectAllSpecs(p: any) {
  selectedProducts.value = selectedProducts.value.filter(s => s.shopping_id !== p.shopping_id)
}
function isProductPartiallySelected(p: any) {
  if (!p.specifications?.length) return false
  const cnt = p.specifications.filter((sp: any) => isSpecSelected(p.shopping_id, sp.specification_id)).length
  return cnt > 0 && cnt < p.specifications.length
}
function isProductFullySelected(p: any) {
  if (!p.specifications?.length) return isWholeProductSelected(p)
  return p.specifications.every((sp: any) => isSpecSelected(p.shopping_id, sp.specification_id))
}
function toggleExpandProduct(p: any) {
  if (!p.specifications?.length) return
  expandedProduct.value = expandedProduct.value === p.shopping_id ? null : p.shopping_id
}

const detailVisible = ref(false)
const detail = ref<any>(null)

function typeLabel(t: string) {
  return { full_reduction: '满减', discount: '折扣', fixed_amount: '固定金额' }[t] || t
}
function typeTag(t: string) {
  return { full_reduction: 'warning', discount: 'success', fixed_amount: '' }[t] || 'info'
}
function statusLabel(s: string) {
  return { draft: '草稿', active: '已上线', paused: '已暂停', expired: '已过期' }[s] || s
}
function statusTag(s: string) {
  return { draft: 'info', active: 'success', paused: 'warning', expired: 'danger' }[s] || 'info'
}

async function loadList(p: number) {
  loading.value = true
  page.value = p
  try {
    const params: Record<string, any> = { page: p, page_size: pageSize.value, ...mallParam() }
    if (filterStatus.value) params.status = filterStatus.value
    const { data } = await API.get('/buyer_coupon/list', { params, headers })
    if (data.current) {
      list.value = data.list
      total.value = data.total
    } else {
      ElMessage.warning(data.msg)
    }
  } catch {
    ElMessage.error('获取优惠券列表失败')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  form.value = {
    name: '', coupon_type: 'full_reduction', min_order_amount: 0,
    discount_value: 10, max_discount: null, total_count: 0,
    per_user_limit: 1, scope: 'store',
    timeRange: null, description: '',
  }
  selectedProducts.value = []
  productOptions.value = []
  productSearched.value = false
  productSearch.value = ''
  expandedProduct.value = null
  createVisible.value = true
}

async function submitCreate() {
  const f = form.value
  if (!f.name?.trim()) return ElMessage.warning('请输入优惠券名称')
  if (!f.timeRange || f.timeRange.length < 2) return ElMessage.warning('请选择有效期')

  if (f.scope === 'product' && selectedProducts.value.length === 0) {
    return ElMessage.warning('请选择至少一个商品')
  }

  submitting.value = true
  try {
    const body: Record<string, any> = {
      name: f.name, coupon_type: f.coupon_type,
      discount_value: f.discount_value, min_order_amount: f.min_order_amount,
      start_time: f.timeRange[0], end_time: f.timeRange[1],
      scope: f.scope, platform_scope: 'all',
      max_discount: f.max_discount, total_count: f.total_count,
      per_user_limit: f.per_user_limit, description: f.description,
    }
    if (f.scope === 'product') {
      body.product_ids = selectedProducts.value.map(s => ({
        mall_id: s.mall_id,
        shopping_id: s.shopping_id,
        specification_id: s.specification_id ?? undefined,
      }))
    }
    const { data } = await API.post('/buyer_coupon/create', body, { params: mallParam(), headers })
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
    const { data } = await API.post('/buyer_coupon/status', { coupon_id: id, status }, { params: mallParam(), headers })
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

async function deleteCoupon(id: number) {
  try {
    const { data } = await API.post('/buyer_coupon/delete', { coupon_id: id }, { params: mallParam(), headers })
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
    const { data } = await API.get('/buyer_coupon/detail', { params: { coupon_id: id, ...mallParam() }, headers })
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
.coupon-manage { padding: 4px; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px; }
.toolbar-right { display: flex; align-items: center; }
.loading-box, .empty-box { padding: 60px 0; }
.pager { margin-top: 16px; display: flex; justify-content: flex-end; }

.product-picker { width: 100%; }
.product-picker__search { display: flex; gap: 8px; margin-bottom: 12px; }
.product-picker__loading { padding: 16px 0; }
.product-picker__list {
  max-height: 240px;
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
  position: relative;
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
.product-picker__spec-actions {
  display: flex;
  padding: 4px 0 2px;
  border-top: 1px dashed var(--el-border-color-lighter);
  margin-top: 4px;
}

.selected-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
.selected-tag-item { display: inline-flex; }

.product-picker__selected {
  margin-top: 12px;
  padding: 10px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}
.product-picker__selected-title {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 6px;
  font-weight: 500;
}
</style>
