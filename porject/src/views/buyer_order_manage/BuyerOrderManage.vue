<template>
  <el-container>
    <el-container>
      <BuyerNavigation />
      <el-container>
        <el-header>
          <BuyerHead />
        </el-header>
        <el-main>
          <div class="order-management-container">
            <h2 class="page-title">订单管理中心</h2>
            <p class="page-subtitle">高效管理您的订单，掌握资金动态</p>

            <!-- Tab 切换 -->
            <div class="om-tabs">
              <div
                v-for="tab in tabs"
                :key="tab.key"
                class="om-tab"
                :class="{ active: activeTab === tab.key }"
                @click="switchTab(tab.key)"
              >
                {{ tab.label }}
                <span v-if="tab.count > 0" class="om-tab-badge">{{ tab.count }}</span>
              </div>
            </div>

            <!-- 搜索栏 -->
            <div class="om-search">
              <el-input
                v-model="keyword"
                placeholder="搜索订单号 / 收货人"
                clearable
                @clear="doSearch"
                @keyup.enter="doSearch"
                style="width: 300px"
              />
              <el-button type="primary" @click="doSearch">搜索</el-button>
            </div>

            <!-- 加载中 -->
            <div v-if="loading" class="om-loading">
              <el-icon class="is-loading" :size="32"><Loading /></el-icon>
              <p>加载中...</p>
            </div>

            <!-- 订单列表 -->
            <template v-if="activeTab === 'orders' || activeTab === 'pending_ship'">
              <div v-if="!loading && orders.length === 0" class="om-empty">暂无订单</div>
              <div v-for="order in orders" :key="order.order_no" class="om-card">
                <div class="om-card-header">
                  <span class="om-order-no">{{ order.order_no }}</span>
                  <span class="om-status" :class="'st-' + order.status">{{ statusText(order.status) }}</span>
                </div>
                <div class="om-card-body">
                  <div class="om-products">
                    <div v-for="(p, i) in order.products" :key="i" class="om-product-row">
                      <span class="om-pname">{{ p.product_name }}</span>
                      <span class="om-spec">{{ p.spec_name }}</span>
                      <span class="om-qty">x{{ p.quantity }}</span>
                      <span class="om-price">¥{{ p.subtotal.toFixed(2) }}</span>
                    </div>
                  </div>
                  <div class="om-info-row">
                    <span>买家：{{ order.user }}</span>
                    <span>收货人：{{ order.receiver_name || '-' }}</span>
                    <span>总额：<b>¥{{ order.total_amount.toFixed(2) }}</b></span>
                  </div>
                  <div class="om-info-row">
                    <span>下单时间：{{ order.created_at }}</span>
                    <span v-if="order.paid_at">支付时间：{{ order.paid_at }}</span>
                  </div>
                  <div v-if="order.escrow" class="om-escrow-info">
                    <span>担保状态：{{ escrowText(order.escrow.status) }}</span>
                    <span>平台抽成：¥{{ order.escrow.platform_commission.toFixed(2) }}</span>
                    <span>实收金额：<b>¥{{ order.escrow.seller_amount.toFixed(2) }}</b></span>
                  </div>
                </div>
              </div>
            </template>

            <!-- 退款列表 -->
            <template v-if="activeTab === 'refunds'">
              <div v-if="!loading && refunds.length === 0" class="om-empty">暂无退款申请</div>
              <div v-for="r in refunds" :key="r.refund_no" class="om-card refund-card">
                <div class="om-card-header">
                  <span class="om-order-no">退款单：{{ r.refund_no }}</span>
                  <span class="om-status" :class="'rst-' + r.status">{{ refundStatusText(r.status) }}</span>
                </div>
                <div class="om-card-body">
                  <div class="om-info-row">
                    <span>关联订单：{{ r.order_no }}</span>
                    <span>买家：{{ r.user }}</span>
                    <span>退款金额：<b>¥{{ r.amount.toFixed(2) }}</b></span>
                  </div>
                  <div class="om-info-row" v-if="r.reason">
                    <span>退款原因：{{ r.reason }}</span>
                  </div>
                  <div class="om-info-row">
                    <span>申请时间：{{ r.created_at }}</span>
                  </div>
                  <div v-if="r.status === 'pending'" class="om-actions">
                    <el-button type="success" size="small" @click="openReview(r, 'approve')">同意退款</el-button>
                    <el-button type="danger" size="small" @click="openReview(r, 'reject')">拒绝退款</el-button>
                  </div>
                  <div v-if="r.seller_remark" class="om-remark">
                    审核备注：{{ r.seller_remark }}
                  </div>
                </div>
              </div>
            </template>

            <!-- 资金明细 -->
            <template v-if="activeTab === 'escrow'">
              <div v-if="!loading && escrowList.length === 0" class="om-empty">暂无资金记录</div>
              <div v-for="e in escrowList" :key="e.order_no" class="om-card escrow-card">
                <div class="om-card-header">
                  <span class="om-order-no">{{ e.order_no }}</span>
                  <span class="om-status" :class="'est-' + e.status">{{ escrowText(e.status) }}</span>
                </div>
                <div class="om-card-body">
                  <div class="om-info-row">
                    <span>买家：{{ e.user }}</span>
                    <span>订单金额：¥{{ e.amount.toFixed(2) }}</span>
                    <span>抽成比例：{{ (e.platform_rate * 100).toFixed(1) }}%</span>
                  </div>
                  <div class="om-info-row">
                    <span>平台抽成：¥{{ e.platform_commission.toFixed(2) }}</span>
                    <span>实收金额：<b>¥{{ e.seller_amount.toFixed(2) }}</b></span>
                  </div>
                  <div class="om-info-row">
                    <span>创建时间：{{ e.created_at }}</span>
                    <span v-if="e.released_at">释放时间：{{ e.released_at }}</span>
                  </div>
                </div>
              </div>
            </template>

            <!-- 分页 -->
            <div class="om-pagination" v-if="total > 0">
              <el-pagination
                v-model:current-page="page"
                v-model:page-size="pageSize"
                :total="total"
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next"
                @current-change="fetchData"
                @size-change="fetchData"
              />
            </div>

            <!-- 审核弹窗 -->
            <el-dialog v-model="reviewVisible" :title="reviewAction === 'approve' ? '同意退款' : '拒绝退款'" width="480px">
              <el-form>
                <el-form-item label="退款单号">
                  <span>{{ reviewRefund?.refund_no }}</span>
                </el-form-item>
                <el-form-item label="退款金额">
                  <span>¥{{ reviewRefund?.amount.toFixed(2) }}</span>
                </el-form-item>
                <el-form-item label="审核备注">
                  <el-input v-model="reviewRemark" type="textarea" :rows="3" placeholder="请输入审核备注（可选）" />
                </el-form-item>
              </el-form>
              <template #footer>
                <el-button @click="reviewVisible = false">取消</el-button>
                <el-button
                  :type="reviewAction === 'approve' ? 'success' : 'danger'"
                  :loading="reviewLoading"
                  @click="submitReview"
                >
                  {{ reviewAction === 'approve' ? '确认同意' : '确认拒绝' }}
                </el-button>
              </template>
            </el-dialog>
          </div>
        </el-main>
      </el-container>
    </el-container>
    <el-footer class="footer-content">版权所有 ©[xb商城]，保留所有权利。</el-footer>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import BuyerNavigation from '@/moon/buyer_navigation.vue'
import BuyerHead from '@/moon/buyer_head.vue'
import BuyerTheme from '@/moon/buyer_theme'

defineOptions({ name: 'BuyerOrderManage' })

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const getHeaders = () => {
  const token = localStorage.getItem('buyer_access_token')
  return token ? { 'Access-Token': token } : {}
}

interface Product { product_name: string; spec_name: string; price: number; quantity: number; subtotal: number }
interface Escrow { amount: number; platform_commission: number; seller_amount: number; status: string; released_at: string | null }
interface Order {
  order_no: string; user: string; total_amount: number; status: string
  receiver_name: string; receiver_phone: string; receiver_addr: string
  created_at: string; paid_at: string | null; shipped_at: string | null
  received_at: string | null; closed_at: string | null
  products: Product[]; escrow: Escrow | null
}
interface RefundItem {
  refund_no: string; order_no: string; user: string; amount: number
  reason: string | null; status: string; seller_remark: string | null
  created_at: string; reviewed_at: string | null
}
interface EscrowItem {
  order_no: string; user: string; amount: number; platform_rate: number
  platform_commission: number; seller_amount: number; status: string
  released_at: string | null; created_at: string
}

const tabs = ref([
  { key: 'orders', label: '全部订单', count: 0 },
  { key: 'pending_ship', label: '待发货', count: 0 },
  { key: 'refunds', label: '退款申请', count: 0 },
  { key: 'escrow', label: '资金明细', count: 0 },
])
const activeTab = ref('orders')
const keyword = ref('')
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const orders = ref<Order[]>([])
const refunds = ref<RefundItem[]>([])
const escrowList = ref<EscrowItem[]>([])

const reviewVisible = ref(false)
const reviewRefund = ref<RefundItem | null>(null)
const reviewAction = ref<'approve' | 'reject'>('approve')
const reviewRemark = ref('')
const reviewLoading = ref(false)

function statusText(s: string) {
  const map: Record<string, string> = {
    pending: '待支付', paid: '已支付', shipped: '已发货',
    received: '已收货', closed: '已关闭', refunded: '已退款', refund_pending: '退款中',
  }
  return map[s] || s
}

function refundStatusText(s: string) {
  const map: Record<string, string> = {
    pending: '待审核', approved: '已同意', rejected: '已拒绝',
    dispute: '平台介入中', platform_approved: '平台判买家胜',
    platform_rejected: '平台判卖家胜', refunded: '已退款',
  }
  return map[s] || s
}

function escrowText(s: string) {
  const map: Record<string, string> = { holding: '冻结中', released: '已释放', refunded: '已退回' }
  return map[s] || s
}

function switchTab(key: string) {
  activeTab.value = key
  page.value = 1
  keyword.value = ''
  fetchData()
}

function doSearch() {
  page.value = 1
  fetchData()
}

async function fetchData() {
  loading.value = true
  try {
    const tab = activeTab.value
    if (tab === 'orders' || tab === 'pending_ship') {
      const params: Record<string, any> = { page: page.value, page_size: pageSize.value }
      if (tab === 'pending_ship') params.status = 'paid'
      if (keyword.value) params.keyword = keyword.value
      const res = await Axios.get('/seller/order/list', { params, headers: getHeaders() })
      if (res.data?.success) {
        orders.value = res.data.data
        total.value = res.data.total
      }
    } else if (tab === 'refunds') {
      const params: Record<string, any> = { page: page.value, page_size: pageSize.value }
      if (keyword.value) params.keyword = keyword.value
      const res = await Axios.get('/seller/order/refund_list', { params, headers: getHeaders() })
      if (res.data?.success) {
        refunds.value = res.data.data
        total.value = res.data.total
      }
    } else if (tab === 'escrow') {
      const params: Record<string, any> = { page: page.value, page_size: pageSize.value }
      const res = await Axios.get('/seller/order/escrow_list', { params, headers: getHeaders() })
      if (res.data?.success) {
        escrowList.value = res.data.data
        total.value = res.data.total
      }
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function openReview(r: RefundItem, action: 'approve' | 'reject') {
  reviewRefund.value = r
  reviewAction.value = action
  reviewRemark.value = ''
  reviewVisible.value = true
}

async function submitReview() {
  if (!reviewRefund.value) return
  reviewLoading.value = true
  try {
    const res = await Axios.post('/seller/order/refund_review', {
      refund_no: reviewRefund.value.refund_no,
      action: reviewAction.value,
      remark: reviewRemark.value || null,
    }, { headers: getHeaders() })
    if (res.data?.success) {
      ElMessage.success(res.data.msg)
      reviewVisible.value = false
      fetchData()
    } else {
      ElMessage.error(res.data?.msg || '操作失败')
    }
  } catch {
    ElMessage.error('操作失败')
  } finally {
    reviewLoading.value = false
  }
}

onMounted(() => {
  new BuyerTheme().initTheme()
  fetchData()
})
</script>

<style scoped>
.el-header {
  border-bottom: 1px solid #514d4d;
  padding-bottom: 10px;
  margin-bottom: 10px;
}
.order-management-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
.page-title {
  text-align: center;
  font-size: 32px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
}
.page-subtitle {
  text-align: center;
  font-size: 16px;
  color: #7f8c8d;
  margin-bottom: 40px;
}
.om-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  background: var(--el-bg-color);
  border-radius: 10px;
  padding: 4px;
}
.om-tab {
  padding: 8px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  position: relative;
  color: var(--el-text-color-regular);
}
.om-tab:hover { background: var(--el-fill-color-light); }
.om-tab.active {
  background: var(--el-color-primary);
  color: #fff;
  font-weight: 500;
}
.om-tab-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #f56c6c;
  color: #fff;
  border-radius: 10px;
  padding: 0 6px;
  font-size: 11px;
  min-width: 18px;
  text-align: center;
}
.om-search {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.om-loading {
  text-align: center;
  padding: 60px 0;
  color: var(--el-text-color-secondary);
}
.om-empty {
  text-align: center;
  padding: 60px 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
.om-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  transition: box-shadow 0.2s;
}
.om-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.om-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.om-order-no {
  font-weight: 500;
  font-size: 14px;
  color: var(--el-text-color-primary);
}
.om-status {
  font-size: 13px;
  padding: 2px 10px;
  border-radius: 12px;
  font-weight: 500;
}
.st-pending, .rst-pending { background: #fef0e0; color: #e6a23c; }
.st-paid { background: #e0f5ea; color: #67c23a; }
.st-shipped { background: #e0ecff; color: #409eff; }
.st-received { background: #e0f5ea; color: #67c23a; }
.st-closed, .st-refunded { background: #f0f0f0; color: #909399; }
.st-refund_pending, .rst-dispute { background: #fde2e2; color: #f56c6c; }
.rst-approved, .rst-refunded { background: #e0f5ea; color: #67c23a; }
.rst-rejected, .rst-platform_rejected { background: #f0f0f0; color: #909399; }
.rst-platform_approved { background: #e0ecff; color: #409eff; }
.est-holding { background: #fef0e0; color: #e6a23c; }
.est-released { background: #e0f5ea; color: #67c23a; }
.est-refunded { background: #f0f0f0; color: #909399; }
.om-card-body { font-size: 13px; color: var(--el-text-color-regular); }
.om-products {
  margin-bottom: 10px;
}
.om-product-row {
  display: flex;
  gap: 12px;
  padding: 4px 0;
  align-items: center;
}
.om-pname { flex: 1; font-weight: 500; }
.om-spec { color: var(--el-text-color-secondary); min-width: 80px; }
.om-qty { min-width: 40px; }
.om-price { font-weight: 600; color: var(--el-color-danger); min-width: 80px; text-align: right; }
.om-info-row {
  display: flex;
  gap: 24px;
  padding: 3px 0;
  flex-wrap: wrap;
}
.om-escrow-info {
  display: flex;
  gap: 24px;
  padding: 6px 0;
  margin-top: 6px;
  border-top: 1px dashed var(--el-border-color-lighter);
  color: var(--el-text-color-secondary);
}
.om-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--el-border-color-lighter);
}
.om-remark {
  margin-top: 8px;
  padding: 8px 12px;
  background: var(--el-fill-color-lighter);
  border-radius: 6px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.om-pagination {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}
.footer-content {
  text-align: center;
  color: darkgray;
}
</style>
