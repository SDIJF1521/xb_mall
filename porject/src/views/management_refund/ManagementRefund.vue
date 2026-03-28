<template>
  <div class="refund-manage-page">
    <ManagementNavigation />
    <div class="refund-manage-content">
      <div class="rm-header">
        <h2>纠纷管理</h2>
        <span class="rm-total" v-if="total > 0">共 {{ total }} 条记录</span>
      </div>

      <!-- 筛选栏 -->
      <div class="rm-toolbar">
        <div class="rm-tabs">
          <div
            v-for="tab in tabs"
            :key="tab.value"
            class="rm-tab"
            :class="{ active: activeTab === tab.value }"
            @click="switchTab(tab.value)"
          >
            {{ tab.label }}
          </div>
        </div>
        <div class="rm-search">
          <el-input
            v-model="keyword"
            placeholder="搜索退款单号 / 订单号 / 用户名"
            clearable
            @clear="doSearch"
            @keyup.enter="doSearch"
            style="width: 300px"
          />
          <el-button type="primary" @click="doSearch">搜索</el-button>
        </div>
      </div>

      <!-- 加载 -->
      <div v-if="loading" class="rm-loading">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <p>加载中...</p>
      </div>

      <!-- 空态 -->
      <div v-else-if="refunds.length === 0" class="rm-empty">
        <el-empty description="暂无纠纷记录" />
      </div>

      <!-- 列表 -->
      <div v-else class="rm-list">
        <div v-for="r in refunds" :key="r.refund_no" class="rm-card">
          <div class="rm-card-header">
            <div class="rm-card-left">
              <span class="rm-refund-no">{{ r.refund_no }}</span>
              <span class="rm-divider">|</span>
              <span class="rm-order-no">订单：{{ r.order_no }}</span>
            </div>
            <span class="rm-status" :class="'rs-' + r.status">{{ statusText(r.status) }}</span>
          </div>
          <div class="rm-card-body">
            <div class="rm-info-grid">
              <div class="rm-info-item">
                <span class="rm-info-label">店铺ID</span>
                <span class="rm-info-value">{{ r.mall_id }}</span>
              </div>
              <div class="rm-info-item">
                <span class="rm-info-label">买家</span>
                <span class="rm-info-value">{{ r.user }}</span>
              </div>
              <div class="rm-info-item">
                <span class="rm-info-label">退款金额</span>
                <span class="rm-info-value rm-amount">¥{{ r.amount.toFixed(2) }}</span>
              </div>
              <div class="rm-info-item">
                <span class="rm-info-label">申请时间</span>
                <span class="rm-info-value">{{ r.created_at }}</span>
              </div>
            </div>
            <div v-if="r.reason" class="rm-reason">
              <span class="rm-reason-label">退款原因：</span>{{ r.reason }}
            </div>
            <div v-if="r.seller_remark" class="rm-remark">
              <span class="rm-remark-label">卖家备注：</span>{{ r.seller_remark }}
            </div>
            <div v-if="r.platform_remark" class="rm-remark">
              <span class="rm-remark-label">平台备注：</span>{{ r.platform_remark }}
              <span v-if="r.platform_admin" class="rm-admin">（处理人：{{ r.platform_admin }}）</span>
            </div>
          </div>
          <div v-if="r.status === 'dispute'" class="rm-card-actions">
            <el-button type="success" @click="openResolve(r, 'approve')">支持买家（退款）</el-button>
            <el-button type="warning" @click="openResolve(r, 'reject')">支持卖家（驳回）</el-button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="rm-pagination" v-if="total > 0">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          background
          @current-change="fetchList"
          @size-change="fetchList"
        />
      </div>

      <!-- 仲裁弹窗 -->
      <el-dialog v-model="resolveVisible" :title="resolveAction === 'approve' ? '支持买家（执行退款）' : '支持卖家（驳回纠纷）'" width="500px">
        <div v-if="resolveRefund" style="margin-bottom: 16px;">
          <p>退款单：{{ resolveRefund.refund_no }}</p>
          <p>订单号：{{ resolveRefund.order_no }}</p>
          <p>买家：{{ resolveRefund.user }}</p>
          <p>退款金额：<b style="color:#f56c6c">¥{{ resolveRefund.amount.toFixed(2) }}</b></p>
          <p v-if="resolveRefund.reason">退款原因：{{ resolveRefund.reason }}</p>
          <p v-if="resolveRefund.seller_remark">卖家备注：{{ resolveRefund.seller_remark }}</p>
        </div>
        <el-input
          v-model="resolveRemark"
          type="textarea"
          :rows="3"
          placeholder="请输入仲裁备注"
        />
        <template #footer>
          <el-button @click="resolveVisible = false">取消</el-button>
          <el-button
            :type="resolveAction === 'approve' ? 'success' : 'warning'"
            :loading="resolveLoading"
            @click="submitResolve"
          >
            {{ resolveAction === 'approve' ? '确认退款' : '确认驳回' }}
          </el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import ManagementNavigation from '@/moon/management_navigation.vue'

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const getHeaders = () => {
  const token = localStorage.getItem('admin_access_token')
  return token ? { 'Access-Token': token } : {}
}

interface RefundItem {
  refund_no: string; order_no: string; mall_id: number; user: string
  amount: number; reason: string | null; status: string
  seller_remark: string | null; platform_remark: string | null
  platform_admin: string | null
  created_at: string; reviewed_at: string | null; resolved_at: string | null
}

const tabs = [
  { label: '待仲裁', value: 'dispute' },
  { label: '全部纠纷', value: '' },
  { label: '已判买家胜', value: 'platform_approved' },
  { label: '已判卖家胜', value: 'platform_rejected' },
  { label: '已退款', value: 'refunded' },
]
const activeTab = ref('dispute')
const keyword = ref('')
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const refunds = ref<RefundItem[]>([])

const resolveVisible = ref(false)
const resolveRefund = ref<RefundItem | null>(null)
const resolveAction = ref<'approve' | 'reject'>('approve')
const resolveRemark = ref('')
const resolveLoading = ref(false)

function statusText(s: string) {
  const map: Record<string, string> = {
    pending: '待卖家审核', approved: '卖家已同意', rejected: '卖家已拒绝',
    dispute: '待平台仲裁', platform_approved: '平台判买家胜',
    platform_rejected: '平台判卖家胜', refunded: '已退款',
  }
  return map[s] || s
}

function switchTab(val: string) {
  activeTab.value = val
  page.value = 1
  fetchList()
}

function doSearch() {
  page.value = 1
  fetchList()
}

async function fetchList() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: pageSize.value }
    if (activeTab.value) params.status = activeTab.value
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    const res = await Axios.get('/manage/refund/list', { params, headers: getHeaders() })
    if (res.data?.success) {
      refunds.value = res.data.data
      total.value = res.data.total
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function openResolve(r: RefundItem, action: 'approve' | 'reject') {
  resolveRefund.value = r
  resolveAction.value = action
  resolveRemark.value = ''
  resolveVisible.value = true
}

async function submitResolve() {
  if (!resolveRefund.value) return
  resolveLoading.value = true
  try {
    const res = await Axios.post('/manage/refund/resolve', {
      refund_no: resolveRefund.value.refund_no,
      action: resolveAction.value,
      remark: resolveRemark.value || null,
    }, { headers: getHeaders() })
    if (res.data?.success) {
      ElMessage.success(res.data.msg)
      resolveVisible.value = false
      fetchList()
    } else {
      ElMessage.error(res.data?.msg || '操作失败')
    }
  } catch {
    ElMessage.error('操作失败')
  } finally {
    resolveLoading.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.refund-manage-page {
  min-height: 100vh;
  background: var(--el-bg-color-page);
}
.refund-manage-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
.rm-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 20px;
}
.rm-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
}
.rm-total {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.rm-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
}
.rm-tabs {
  display: flex;
  gap: 4px;
  background: var(--el-bg-color);
  border-radius: 10px;
  padding: 4px;
}
.rm-tab {
  padding: 6px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  color: var(--el-text-color-regular);
}
.rm-tab:hover { background: var(--el-fill-color-light); }
.rm-tab.active {
  background: var(--el-color-primary);
  color: #fff;
  font-weight: 500;
}
.rm-search {
  display: flex;
  gap: 8px;
}
.rm-loading, .rm-empty {
  text-align: center;
  padding: 60px 0;
  color: var(--el-text-color-secondary);
}
.rm-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  transition: box-shadow 0.2s;
}
.rm-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.rm-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.rm-card-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.rm-refund-no {
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-primary);
}
.rm-divider { color: var(--el-border-color); }
.rm-order-no { font-size: 13px; color: var(--el-text-color-secondary); }
.rm-status {
  font-size: 12px;
  padding: 3px 12px;
  border-radius: 12px;
  font-weight: 500;
}
.rs-dispute { background: #fde2e2; color: #f56c6c; }
.rs-platform_approved { background: #e0f5ea; color: #67c23a; }
.rs-platform_rejected { background: #f0f0f0; color: #909399; }
.rs-refunded { background: #e0ecff; color: #409eff; }
.rs-pending { background: #fef0e0; color: #e6a23c; }
.rs-approved { background: #e0f5ea; color: #67c23a; }
.rs-rejected { background: #f0f0f0; color: #909399; }
.rm-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px 24px;
  margin-bottom: 10px;
}
.rm-info-item {
  display: flex;
  gap: 6px;
  font-size: 13px;
}
.rm-info-label {
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}
.rm-info-value {
  color: var(--el-text-color-primary);
}
.rm-amount {
  font-weight: 600;
  color: #f56c6c;
}
.rm-reason, .rm-remark {
  font-size: 13px;
  padding: 6px 10px;
  margin-top: 6px;
  background: var(--el-fill-color-lighter);
  border-radius: 6px;
  color: var(--el-text-color-regular);
}
.rm-reason-label, .rm-remark-label {
  color: var(--el-text-color-secondary);
  font-weight: 500;
}
.rm-admin {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}
.rm-card-actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}
.rm-pagination {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}
</style>
