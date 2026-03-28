<template>
  <div class="orders-page">
    <!-- 页头 -->
    <div class="orders-page__header">
      <h2 class="orders-page__title">我的订单</h2>
      <span class="orders-page__total-hint" v-if="total > 0">共 {{ total }} 笔订单</span>
    </div>

    <!-- 搜索栏 + 状态标签栏 -->
    <div class="orders-toolbar">
      <div class="orders-tab-bar">
        <div
          v-for="tab in tabs"
          :key="tab.value"
          class="orders-tab-bar__item"
          :class="{ 'is-active': activeTab === tab.value }"
          @click="switchTab(tab.value)"
        >
          {{ tab.label }}
        </div>
      </div>
      <div class="orders-search">
        <div class="orders-search__box">
          <svg class="orders-search__icon" viewBox="0 0 20 20" width="16" height="16" fill="none">
            <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" stroke-width="1.8"/>
            <path d="M13 13l4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
          </svg>
          <input
            v-model="keyword"
            class="orders-search__input"
            type="text"
            placeholder="搜索订单号 / 商品名 / 收货人"
            @keydown.enter="doSearch"
          />
          <button v-if="keyword" class="orders-search__clear" @click="clearSearch">
            <svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor">
              <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm2.8 4.2a.6.6 0 01.84.85L9.25 8.43l2.4 2.38a.6.6 0 01-.85.84L8.42 9.26l-2.38 2.4a.6.6 0 01-.84-.85L7.58 8.43l-2.4-2.38a.6.6 0 01.85-.84L8.42 7.6l2.38-2.4z"/>
            </svg>
          </button>
        </div>
        <button class="btn btn--primary btn--search" @click="doSearch">搜索</button>
      </div>
    </div>

    <!-- 加载骨架 -->
    <div v-if="loading" class="orders-page__loading">
      <div v-for="n in 3" :key="n" class="skeleton-card">
        <div class="skeleton-line w60"></div>
        <div class="skeleton-line w90"></div>
        <div class="skeleton-line w40"></div>
      </div>
    </div>

    <!-- 空态 -->
    <div v-else-if="orders.length === 0" class="orders-empty">
      <div class="orders-empty__icon">
        <svg viewBox="0 0 80 80" width="80" height="80" fill="none">
          <rect x="12" y="18" width="56" height="48" rx="6" stroke="currentColor" stroke-width="2"/>
          <path d="M12 30h56" stroke="currentColor" stroke-width="2"/>
          <rect x="24" y="40" width="32" height="4" rx="2" fill="currentColor" opacity="0.2"/>
          <rect x="28" y="50" width="24" height="4" rx="2" fill="currentColor" opacity="0.15"/>
        </svg>
      </div>
      <p class="orders-empty__text">暂无订单记录</p>
    </div>

    <!-- 订单列表 -->
    <div v-else class="orders-list">
      <div
        v-for="(order, index) in orders"
        :key="order.order_no"
        class="order-card"
        :style="{ animationDelay: `${index * 0.06}s` }"
      >
        <!-- 卡片头：店铺 + 订单号 + 状态 -->
        <div class="order-card__head">
          <div class="order-card__meta">
            <span class="order-card__no">{{ order.order_no }}</span>
            <span class="order-card__time">{{ order.created_at }}</span>
          </div>
          <span class="order-card__status" :class="'is-' + order.status">
            {{ statusText(order.status) }}
          </span>
        </div>

        <!-- 商品行 -->
        <div class="order-card__body">
          <div
            v-for="(item, idx) in order.items"
            :key="idx"
            class="order-goods"
          >
            <div class="order-goods__info">
              <span class="order-goods__name">{{ item.product_name }}</span>
              <span class="order-goods__spec" v-if="item.spec_name">{{ item.spec_name }}</span>
            </div>
            <div class="order-goods__numbers">
              <span class="order-goods__price">¥{{ item.price.toFixed(2) }}</span>
              <span class="order-goods__qty">×{{ item.quantity }}</span>
              <span class="order-goods__subtotal">¥{{ item.subtotal.toFixed(2) }}</span>
            </div>
          </div>
        </div>

        <!-- 卡片底：合计 + 操作 -->
        <div class="order-card__foot">
          <div class="order-card__summary">
            <span class="order-card__summary-label">合计</span>
            <span class="order-card__summary-amount">¥{{ order.total_amount.toFixed(2) }}</span>
          </div>

          <div class="order-card__actions">
            <!-- 待支付 -->
            <template v-if="order.status === 'pending'">
              <span class="order-card__countdown" v-if="getCountdown(order) > 0">
                {{ formatCountdown(getCountdown(order)) }}
              </span>
              <button class="btn btn--primary" @click="handlePay(order)" :disabled="payLoading === order.order_no">
                {{ payLoading === order.order_no ? '跳转中...' : '立即支付' }}
              </button>
              <button class="btn btn--ghost" @click="handleCancel(order)" :disabled="cancelLoading === order.order_no">
                取消
              </button>
            </template>

            <!-- 已支付 / 已发货 -->
            <template v-if="order.status === 'paid' || order.status === 'shipped'">
              <span class="order-card__escrow-tag">担保中</span>
              <button class="btn btn--success" @click="handleConfirm(order)" :disabled="confirmLoading === order.order_no">
                确认收货
              </button>
              <button class="btn btn--warning" @click="openRefundDialog(order)">
                申请退款
              </button>
            </template>

            <!-- 退款中 -->
            <template v-if="order.status === 'refund_pending'">
              <span class="order-card__refund-pending-tag">退款审核中</span>
              <button class="btn btn--ghost btn--sm" @click="checkRefundProgress(order)">查看进度</button>
            </template>

            <!-- 已收货 -->
            <template v-if="order.status === 'received'">
              <span class="order-card__done-tag">交易完成</span>
            </template>

            <!-- 已关闭 -->
            <template v-if="order.status === 'closed'">
              <span class="order-card__closed-tag">已关闭</span>
            </template>

            <!-- 已退款 -->
            <template v-if="order.status === 'refunded'">
              <span class="order-card__refund-tag">已退款</span>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- 退款申请弹窗 -->
    <el-dialog v-model="refundDialogVisible" title="申请退款" width="440px" :close-on-click-modal="false">
      <div v-if="refundOrder" style="margin-bottom: 12px; font-size: 14px; color: var(--el-text-color-regular);">
        订单号：{{ refundOrder.order_no }}<br/>
        退款金额：<b style="color: var(--el-color-danger);">¥{{ refundOrder.total_amount.toFixed(2) }}</b>
      </div>
      <el-input
        v-model="refundReason"
        type="textarea"
        :rows="3"
        placeholder="请输入退款原因（可选）"
        maxlength="500"
        show-word-limit
      />
      <p style="margin-top: 8px; font-size: 12px; color: var(--el-text-color-secondary);">
        提交后将由卖家审核，卖家同意后退款将原路退回。如卖家拒绝，您可申请平台介入。
      </p>
      <template #footer>
        <el-button @click="refundDialogVisible = false">取消</el-button>
        <el-button type="warning" :loading="refundApplyLoading" @click="submitRefundApply">提交申请</el-button>
      </template>
    </el-dialog>

    <!-- 分页 -->
    <div class="orders-page__pagination" v-if="total > 0">
      <div class="pagination-info">
        第 {{ (page - 1) * pageSize + 1 }}–{{ Math.min(page * pageSize, total) }} 条，共 {{ total }} 条
      </div>
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[5, 10, 20, 50]"
        layout="sizes, prev, pager, next, jumper"
        background
        @current-change="fetchOrders"
        @size-change="handleSizeChange"
      />
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const API = 'http://127.0.0.1:8000/api'

export default {
  name: 'CenterOrders',
  data() {
    return {
      tabs: [
        { label: '全部', value: 'all' },
        { label: '待支付', value: 'pending' },
        { label: '已支付', value: 'paid' },
        { label: '已发货', value: 'shipped' },
        { label: '退款中', value: 'refund_pending' },
        { label: '已收货', value: 'received' },
        { label: '已关闭', value: 'closed' },
        { label: '已退款', value: 'refunded' },
      ],
      refundDialogVisible: false,
      refundOrder: null,
      refundReason: '',
      refundApplyLoading: false,
      disputeLoading: '',
      activeTab: 'all',
      keyword: '',
      orders: [],
      loading: false,
      page: 1,
      pageSize: 10,
      total: 0,
      payLoading: '',
      cancelLoading: '',
      confirmLoading: '',
      refundLoading: '',
      now: Date.now(),
      timer: null,
    }
  },
  mounted() {
    this.syncPendingOrders()
    this.fetchOrders().then(() => {
      const params = new URLSearchParams(window.location.search)
      const refundOrderNo = params.get('refund')
      if (refundOrderNo) {
        const order = this.orders.find(o => o.order_no === refundOrderNo)
        if (order && (order.status === 'paid' || order.status === 'shipped')) {
          this.openRefundDialog(order)
        }
      }
    })
    this.timer = setInterval(() => { this.now = Date.now() }, 1000)
  },
  beforeUnmount() {
    if (this.timer) clearInterval(this.timer)
  },
  methods: {
    getToken() {
      return localStorage.getItem('access_token') || ''
    },

    switchTab(val) {
      this.activeTab = val
      this.page = 1
      this.fetchOrders()
    },

    doSearch() {
      this.page = 1
      this.fetchOrders()
    },

    clearSearch() {
      this.keyword = ''
      this.page = 1
      this.fetchOrders()
    },

    handleSizeChange() {
      this.page = 1
      this.fetchOrders()
    },

    async syncPendingOrders() {
      let synced = 0
      try {
        const res = await axios.get(`${API}/order/list`, {
          params: { status: 'pending', page: 1, page_size: 50 },
          headers: { 'access-token': this.getToken() },
        })
        if (!res.data?.success) return
        for (const order of (res.data.list || [])) {
          try {
            const r = await axios.post(`${API}/order/sync_pay`, { order_no: order.order_no }, {
              headers: { 'access-token': this.getToken() },
            })
            if (r.data?.success && !r.data?.already_paid) synced++
          } catch {}
        }
      } catch {}
      if (synced > 0) {
        ElMessage.success(`已自动确认 ${synced} 笔支付成功的订单`)
        this.fetchOrders()
      }
    },

    async fetchOrders() {
      this.loading = true
      try {
        const params = { page: this.page, page_size: this.pageSize }
        if (this.activeTab !== 'all') params.status = this.activeTab
        if (this.keyword.trim()) params.keyword = this.keyword.trim()
        const res = await axios.get(`${API}/order/list`, {
          params,
          headers: { 'access-token': this.getToken() },
        })
        if (res.data?.success) {
          this.orders = res.data.list || []
          this.total = res.data.total || 0
        }
      } catch (e) {
        console.error(e)
      } finally {
        this.loading = false
      }
    },

    statusText(s) {
      return { pending: '待支付', paid: '已支付', shipped: '已发货', received: '已收货', closed: '已关闭', refunded: '已退款', refund_pending: '退款中' }[s] || s
    },

    getCountdown(order) {
      if (!order.expire_at) return 0
      return Math.max(0, Math.floor((new Date(order.expire_at).getTime() - this.now) / 1000))
    },

    formatCountdown(secs) {
      const m = Math.floor(secs / 60)
      const s = secs % 60
      return `${m}:${s < 10 ? '0' + s : s}`
    },

    async handlePay(order) {
      try {
        await ElMessageBox.confirm(
          `订单金额 ¥${order.total_amount.toFixed(2)}，将跳转支付宝完成支付。`,
          '确认支付',
          { confirmButtonText: '前往支付', cancelButtonText: '取消', type: 'info' }
        )
      } catch { return }

      this.payLoading = order.order_no
      try {
        const res = await axios.post(`${API}/order/pay`, {
          order_no: order.order_no,
          pay_method: 'alipay',
          idempotency_key: `pay_${order.order_no}_${Date.now()}`,
        }, { headers: { 'access-token': this.getToken() } })

        if (res.data?.success && res.data.pay_form) {
          const div = document.createElement('div')
          div.innerHTML = res.data.pay_form
          document.body.appendChild(div)
          const form = div.querySelector('form')
          if (form) { form.submit() } else {
            ElMessage.error('支付表单解析失败')
            document.body.removeChild(div)
          }
        } else {
          ElMessage.error(res.data?.msg || '发起支付失败')
        }
      } catch { ElMessage.error('支付请求失败') }
      finally { this.payLoading = '' }
    },

    async handleCancel(order) {
      try { await ElMessageBox.confirm('系统将检查支付宝是否已付款，确认未付款后才会取消订单。', '取消订单', { type: 'warning' }) } catch { return }
      this.cancelLoading = order.order_no
      try {
        const res = await axios.post(`${API}/order/cancel`, { order_no: order.order_no }, { headers: { 'access-token': this.getToken() } })
        if (res.data?.success) { ElMessage.success('订单已取消'); this.fetchOrders() }
        else ElMessage.error(res.data?.msg || '取消失败')
      } catch { ElMessage.error('取消请求失败') }
      finally { this.cancelLoading = '' }
    },

    async handleConfirm(order) {
      try {
        await ElMessageBox.confirm('确认收货后，担保资金将释放给卖家（平台收取 10% 服务费）。确定已收到商品？', '确认收货', { type: 'warning' })
      } catch { return }
      this.confirmLoading = order.order_no
      try {
        const res = await axios.post(`${API}/order/confirm`, { order_no: order.order_no }, { headers: { 'access-token': this.getToken() } })
        if (res.data?.success) { ElMessage.success(res.data.msg || '确认收货成功'); this.fetchOrders() }
        else ElMessage.error(res.data?.msg || '操作失败')
      } catch { ElMessage.error('请求失败') }
      finally { this.confirmLoading = '' }
    },

    openRefundDialog(order) {
      this.refundOrder = order
      this.refundReason = ''
      this.refundDialogVisible = true
    },

    async submitRefundApply() {
      if (!this.refundOrder) return
      this.refundApplyLoading = true
      try {
        const res = await axios.post(`${API}/refund/apply`, {
          order_no: this.refundOrder.order_no,
          reason: this.refundReason || null,
        }, { headers: { 'access-token': this.getToken() } })
        if (res.data?.success) {
          ElMessage.success(res.data.msg || '退款申请已提交')
          this.refundDialogVisible = false
          this.fetchOrders()
        } else {
          ElMessage.error(res.data?.msg || '申请失败')
        }
      } catch { ElMessage.error('退款申请失败') }
      finally { this.refundApplyLoading = false }
    },

    async checkRefundProgress(order) {
      try {
        const res = await axios.get(`${API}/refund/by_order`, {
          params: { order_no: order.order_no },
          headers: { 'access-token': this.getToken() },
        })
        if (res.data?.success && res.data.data) {
          const r = res.data.data
          const statusMap = {
            pending: '等待卖家审核',
            approved: '卖家已同意，退款处理中',
            rejected: '卖家已拒绝',
            dispute: '平台介入中，请等待',
            platform_approved: '平台判买家胜，退款处理中',
            platform_rejected: '平台判卖家胜，纠纷已关闭',
            refunded: '退款已完成',
          }
          const msg = statusMap[r.status] || r.status
          if (r.status === 'rejected') {
            try {
              await ElMessageBox.confirm(
                `退款被卖家拒绝${r.seller_remark ? '（' + r.seller_remark + '）' : ''}，是否申请平台介入？`,
                '退款进度',
                { confirmButtonText: '申请平台介入', cancelButtonText: '暂不处理', type: 'warning' }
              )
              this.handleDispute(r.refund_no)
            } catch { /* user cancelled */ }
          } else {
            ElMessageBox.alert(
              `退款单：${r.refund_no}\n状态：${msg}${r.reason ? '\n原因：' + r.reason : ''}${r.seller_remark ? '\n卖家备注：' + r.seller_remark : ''}${r.platform_remark ? '\n平台备注：' + r.platform_remark : ''}`,
              '退款进度',
              { confirmButtonText: '知道了' }
            )
          }
        } else {
          ElMessage.info('暂无退款记录')
        }
      } catch { ElMessage.error('查询失败') }
    },

    async handleDispute(refundNo) {
      this.disputeLoading = refundNo
      try {
        const res = await axios.post(`${API}/refund/dispute`, { refund_no: refundNo }, {
          headers: { 'access-token': this.getToken() },
        })
        if (res.data?.success) {
          ElMessage.success(res.data.msg || '已申请平台介入')
          this.fetchOrders()
        } else {
          ElMessage.error(res.data?.msg || '操作失败')
        }
      } catch { ElMessage.error('操作失败') }
      finally { this.disputeLoading = '' }
    },
  },
}
</script>

<style scoped>
/* ═══════════════════════ 页面容器 ═══════════════════════ */
.orders-page {
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
  padding: 28px 24px 40px;
}

/* ─── 页头 ─── */
.orders-page__header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 20px;
}

.orders-page__title {
  font-size: 20px;
  font-weight: 600;
  color: var(--vt-c-text-light-1, #303133);
  margin: 0;
  letter-spacing: -0.3px;
}

.orders-page__total-hint {
  font-size: 13px;
  color: var(--vt-c-text-light-2, #909399);
}

/* ─── 工具栏 ─── */
.orders-toolbar {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 24px;
}

/* ─── 搜索栏 ─── */
.orders-search {
  display: flex;
  gap: 8px;
}

.orders-search__box {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  height: 38px;
  border-radius: 10px;
  border: 1px solid var(--color-border, #dcdfe6);
  background: var(--color-background, #fff);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.orders-search__box:focus-within {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
}

.orders-search__icon {
  color: var(--vt-c-text-light-2, #c0c4cc);
  flex-shrink: 0;
}

.orders-search__input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: var(--vt-c-text-light-1, #303133);
}

.orders-search__input::placeholder {
  color: var(--el-text-color-placeholder, #c0c4cc);
}

.orders-search__clear {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  padding: 0;
  border: none;
  background: none;
  color: var(--vt-c-text-light-2, #c0c4cc);
  cursor: pointer;
  border-radius: 50%;
  transition: color 0.15s, background 0.15s;
}

.orders-search__clear:hover {
  color: #909399;
  background: var(--color-background-soft, #f0f0f0);
}

.btn--search {
  height: 38px;
  padding: 0 20px;
  border-radius: 10px;
  font-size: 13px;
  flex-shrink: 0;
}

/* ─── Tab 标签栏（自绘，匹配项目圆角风格） ─── */
.orders-tab-bar {
  display: flex;
  gap: 6px;
  padding: 4px;
  background: var(--color-background-soft, #f5f7fa);
  border-radius: 12px;
  overflow-x: auto;
}

.orders-tab-bar__item {
  padding: 7px 18px;
  font-size: 13px;
  font-weight: 500;
  color: var(--vt-c-text-light-2, #909399);
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.25s ease;
  user-select: none;
}

.orders-tab-bar__item:hover {
  color: var(--vt-c-text-light-1, #303133);
  background: var(--color-background, rgba(255, 255, 255, 0.6));
}

.orders-tab-bar__item.is-active {
  color: #fff;
  background: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

/* ─── 加载骨架 ─── */
.orders-page__loading {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-card {
  padding: 22px 20px;
  border-radius: 16px;
  background: var(--color-background, #fff);
  border: 1px solid var(--color-border, #e4e7ed);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.skeleton-line {
  height: 14px;
  border-radius: 7px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-line.w60 { width: 60%; }
.skeleton-line.w90 { width: 90%; }
.skeleton-line.w40 { width: 40%; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ─── 空态 ─── */
.orders-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64px 0;
  color: var(--vt-c-text-light-2, #c0c4cc);
}

.orders-empty__icon {
  margin-bottom: 16px;
  opacity: 0.5;
}

.orders-empty__text {
  font-size: 14px;
  margin: 0;
}

/* ═══════════════════════ 订单卡片 ═══════════════════════ */
.orders-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.order-card {
  border-radius: 16px;
  border: 1px solid var(--color-border, #e4e7ed);
  background: var(--color-background, #fff);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  animation: fadeInUp 0.45s ease both;
}

.order-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ─── 卡片头部 ─── */
.order-card__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid var(--color-border, #f0f0f0);
}

.order-card__meta {
  display: flex;
  align-items: center;
  gap: 14px;
}

.order-card__no {
  font-size: 13px;
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  color: var(--vt-c-text-light-2, #909399);
  letter-spacing: 0.3px;
}

.order-card__time {
  font-size: 12px;
  color: var(--vt-c-text-light-2, #b0b3bb);
}

.order-card__status {
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 20px;
  letter-spacing: 0.5px;
}

.order-card__status.is-pending {
  color: #e6a23c;
  background: rgba(230, 162, 60, 0.1);
}

.order-card__status.is-paid {
  color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}

.order-card__status.is-shipped {
  color: #909399;
  background: rgba(144, 147, 153, 0.1);
}

.order-card__status.is-received {
  color: #67c23a;
  background: rgba(103, 194, 58, 0.1);
}

.order-card__status.is-closed {
  color: #909399;
  background: rgba(144, 147, 153, 0.08);
}

.order-card__status.is-refunded {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.1);
}

.order-card__status.is-refund_pending {
  color: #e6a23c;
  background: rgba(230, 162, 60, 0.12);
}

/* ─── 商品行 ─── */
.order-card__body {
  padding: 4px 20px;
}

.order-goods {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  gap: 16px;
}

.order-goods + .order-goods {
  border-top: 1px dashed var(--color-border, #ebeef5);
}

.order-goods__info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.order-goods__name {
  font-size: 14px;
  font-weight: 500;
  color: var(--vt-c-text-light-1, #303133);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.order-goods__spec {
  font-size: 12px;
  color: var(--vt-c-text-light-2, #b0b3bb);
  padding: 1px 8px;
  background: var(--color-background-soft, #f5f7fa);
  border-radius: 4px;
  display: inline-block;
  max-width: fit-content;
}

.order-goods__numbers {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.order-goods__price {
  font-size: 13px;
  color: var(--vt-c-text-light-2, #909399);
}

.order-goods__qty {
  font-size: 12px;
  color: var(--vt-c-text-light-2, #b0b3bb);
}

.order-goods__subtotal {
  font-size: 14px;
  font-weight: 600;
  color: var(--vt-c-text-light-1, #303133);
  min-width: 70px;
  text-align: right;
}

/* ─── 卡片底部 ─── */
.order-card__foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-top: 1px solid var(--color-border, #f0f0f0);
  background: var(--color-background-soft, #fafbfc);
}

.order-card__summary {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.order-card__summary-label {
  font-size: 13px;
  color: var(--vt-c-text-light-2, #909399);
}

.order-card__summary-amount {
  font-size: 22px;
  font-weight: 700;
  color: #e74c3c;
  letter-spacing: -0.5px;
}

.order-card__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.order-card__countdown {
  font-size: 12px;
  font-weight: 600;
  font-family: 'SF Mono', 'Menlo', monospace;
  color: #e74c3c;
  background: rgba(231, 76, 60, 0.08);
  padding: 3px 10px;
  border-radius: 20px;
  margin-right: 4px;
}

.order-card__escrow-tag {
  font-size: 11px;
  color: #409eff;
  background: rgba(64, 158, 255, 0.08);
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 500;
}

.order-card__done-tag {
  font-size: 12px;
  color: #67c23a;
  background: rgba(103, 194, 58, 0.08);
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 600;
}

.order-card__closed-tag {
  font-size: 12px;
  color: #909399;
  background: rgba(144, 147, 153, 0.08);
  padding: 4px 12px;
  border-radius: 20px;
}

.order-card__refund-tag {
  font-size: 12px;
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.08);
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 500;
}

.order-card__refund-pending-tag {
  font-size: 12px;
  color: #e6a23c;
  background: rgba(230, 162, 60, 0.1);
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 500;
}

/* ═══════════════════════ 自绘按钮 ═══════════════════════ */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 16px;
  font-size: 13px;
  font-weight: 500;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn--primary {
  color: #fff;
  background: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.25);
}

.btn--primary:hover:not(:disabled) {
  background: #66b1ff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.35);
}

.btn--ghost {
  color: var(--vt-c-text-light-2, #909399);
  background: transparent;
  border: 1px solid var(--color-border, #dcdfe6);
}

.btn--ghost:hover:not(:disabled) {
  color: #409eff;
  border-color: #409eff;
}

.btn--success {
  color: #fff;
  background: #67c23a;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.25);
}

.btn--success:hover:not(:disabled) {
  background: #85ce61;
}

.btn--warning {
  color: #e6a23c;
  background: transparent;
  border: 1px solid #e6a23c;
}

.btn--warning:hover:not(:disabled) {
  color: #fff;
  background: #e6a23c;
}

/* ─── 分页 ─── */
.orders-page__pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 28px;
  padding: 16px 4px 0;
  border-top: 1px solid var(--color-border, #f0f0f0);
}

.pagination-info {
  font-size: 12px;
  color: var(--vt-c-text-light-2, #909399);
  white-space: nowrap;
  flex-shrink: 0;
}

/* ═══════════════════════ 暗色模式 ═══════════════════════ */
html.dark .orders-page__title {
  color: var(--vt-c-text-dark-1, #f0f0f0);
}

html.dark .orders-page__total-hint,
html.dark .order-card__no,
html.dark .order-card__time {
  color: var(--vt-c-text-dark-2, #a0a4ab);
}

html.dark .orders-tab-bar {
  background: var(--vt-c-black-soft, #222);
}

html.dark .orders-tab-bar__item {
  color: var(--vt-c-text-dark-2, #a0a4ab);
}

html.dark .orders-tab-bar__item:hover {
  color: #f0f0f0;
  background: rgba(255, 255, 255, 0.06);
}

html.dark .order-card {
  background: var(--vt-c-black-soft, #1a1a1a);
  border-color: var(--vt-c-divider-dark-2, #2c2c2c);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
}

html.dark .order-card:hover {
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.35);
}

html.dark .order-card__head,
html.dark .order-card__foot {
  border-color: var(--vt-c-divider-dark-2, #2c2c2c);
}

html.dark .order-card__foot {
  background: var(--vt-c-black, #181818);
}

html.dark .order-goods + .order-goods {
  border-color: var(--vt-c-divider-dark-2, #2c2c2c);
}

html.dark .order-goods__name {
  color: var(--vt-c-text-dark-1, #f0f0f0);
}

html.dark .order-goods__spec {
  color: var(--vt-c-text-dark-2, #a0a4ab);
  background: rgba(255, 255, 255, 0.05);
}

html.dark .order-goods__subtotal {
  color: var(--vt-c-text-dark-1, #f0f0f0);
}

html.dark .order-card__summary-amount {
  color: #f56c6c;
}

html.dark .order-card__countdown {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.12);
}

html.dark .skeleton-card {
  background: var(--vt-c-black-soft, #1a1a1a);
  border-color: var(--vt-c-divider-dark-2, #2c2c2c);
}

html.dark .skeleton-line {
  background: linear-gradient(90deg, #2a2a2a 25%, #333 50%, #2a2a2a 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

html.dark .orders-empty {
  color: var(--vt-c-text-dark-2, #666);
}

html.dark .btn--ghost {
  color: var(--vt-c-text-dark-2, #a0a4ab);
  border-color: var(--vt-c-divider-dark-2, #444);
}

html.dark .btn--ghost:hover:not(:disabled) {
  color: #409eff;
  border-color: #409eff;
}

html.dark .orders-search__box {
  background: var(--vt-c-black-soft, #1a1a1a);
  border-color: var(--vt-c-divider-dark-2, #333);
}

html.dark .orders-search__box:focus-within {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.15);
}

html.dark .orders-search__input {
  color: var(--vt-c-text-dark-1, #f0f0f0);
}

html.dark .orders-search__input::placeholder {
  color: var(--vt-c-text-dark-2, #666);
}

html.dark .orders-search__clear:hover {
  background: rgba(255, 255, 255, 0.08);
}

html.dark .pagination-info {
  color: var(--vt-c-text-dark-2, #a0a4ab);
}

html.dark .orders-page__pagination {
  border-color: var(--vt-c-divider-dark-2, #2c2c2c);
}
</style>
