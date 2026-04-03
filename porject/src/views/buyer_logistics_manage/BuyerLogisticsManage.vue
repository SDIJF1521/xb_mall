<template>
  <el-container>
    <el-container>
      <BuyerNavigation />
      <el-container>
        <el-header>
          <BuyerHead />
        </el-header>
        <el-main>
          <div class="logistics-container">
            <h2 class="page-title">物流管理</h2>
            <p class="page-subtitle">查看所有发货记录和物流轨迹</p>

            <!-- 店铺选择 -->
            <div v-if="isOwner && storeList.length > 1" class="lm-store-selector">
              <span class="lm-store-label">当前店铺：</span>
              <el-select
                v-model="selectedMallId"
                placeholder="选择店铺"
                style="width: 240px"
                @change="onStoreChange"
              >
                <el-option
                  v-for="s in storeList"
                  :key="s.id"
                  :label="s.mall_name"
                  :value="s.id"
                />
              </el-select>
            </div>

            <!-- 搜索栏 -->
            <div class="lm-search">
              <el-input
                v-model="keyword"
                placeholder="搜索订单号 / 运单号"
                clearable
                @clear="doSearch"
                @keyup.enter="doSearch"
                style="width: 300px"
              />
              <el-button type="primary" @click="doSearch">搜索</el-button>
            </div>

            <!-- 加载中 -->
            <div v-if="loading" class="lm-loading">
              <el-icon class="is-loading" :size="32"><Loading /></el-icon>
              <p>加载中...</p>
            </div>

            <!-- 列表 -->
            <div v-if="!loading && list.length === 0" class="lm-empty">暂无发货记录</div>
            <div v-for="item in list" :key="item.id" class="lm-card">
              <div class="lm-card-header">
                <div class="lm-card-left">
                  <span class="lm-order-no">{{ item.order_no }}</span>
                  <el-tag size="small" :type="orderStatusType(item.order_status) as any">{{ orderStatusText(item.order_status) }}</el-tag>
                </div>
                <span class="lm-time">{{ item.created_at }}</span>
              </div>
              <div class="lm-card-body">
                <div class="lm-row">
                  <span class="lm-label">快递公司</span>
                  <span class="lm-val">{{ item.express_company }}</span>
                </div>
                <div class="lm-row">
                  <span class="lm-label">运单号</span>
                  <span class="lm-val lm-val--mono">{{ item.tracking_number }}</span>
                </div>
                <div class="lm-row">
                  <span class="lm-label">发件人</span>
                  <span class="lm-val">{{ item.sender_name }} {{ item.sender_phone }}</span>
                </div>
                <div class="lm-row">
                  <span class="lm-label">收货人</span>
                  <span class="lm-val">{{ item.receiver_name || '-' }} {{ item.receiver_phone || '' }}</span>
                </div>
                <div class="lm-row" v-if="item.total_amount">
                  <span class="lm-label">订单金额</span>
                  <span class="lm-val lm-val--price">¥{{ item.total_amount.toFixed(2) }}</span>
                </div>
              </div>
              <div class="lm-card-footer">
                <el-button type="primary" size="small" plain @click="viewDetail(item)">
                  <el-icon><Location /></el-icon> 查看轨迹
                </el-button>
              </div>
            </div>

            <!-- 分页 -->
            <div class="lm-pagination" v-if="total > 0">
              <el-pagination
                v-model:current-page="page"
                v-model:page-size="pageSize"
                :total="total"
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next"
                @current-change="fetchList"
                @size-change="fetchList"
              />
            </div>

            <!-- 物流详情弹窗 -->
            <el-dialog v-model="detailVisible" title="物流轨迹" width="600px" destroy-on-close>
              <div v-if="detailLoading" style="text-align: center; padding: 40px;">
                <el-icon class="is-loading" :size="28"><Loading /></el-icon>
                <p style="color: var(--el-text-color-secondary); margin-top: 8px;">加载中...</p>
              </div>
              <template v-else-if="detailData">
                <div class="lm-detail-info">
                  <div class="lm-row">
                    <span class="lm-label">快递公司</span>
                    <span class="lm-val">{{ detailData.express_company }}</span>
                  </div>
                  <div class="lm-row">
                    <span class="lm-label">运单号</span>
                    <span class="lm-val lm-val--mono">{{ detailData.tracking_number }}</span>
                  </div>
                  <div class="lm-row">
                    <span class="lm-label">发货时间</span>
                    <span class="lm-val">{{ detailData.created_at }}</span>
                  </div>
                </div>
                <div v-if="detailData.routes && detailData.routes.routeResps" style="margin-top: 16px;">
                  <h4 style="margin: 0 0 12px; font-size: 14px; font-weight: 600;">物流轨迹</h4>
                  <el-timeline>
                    <el-timeline-item
                      v-for="(route, idx) in detailData.routes.routeResps[0]?.routes || []"
                      :key="idx"
                      :timestamp="route.acceptTime"
                      placement="top"
                      :type="idx === 0 ? 'primary' : 'info'"
                    >
                      {{ route.remark }}
                    </el-timeline-item>
                  </el-timeline>
                </div>
                <el-empty v-else description="暂无物流轨迹信息（运单可能尚未揽收）" :image-size="60" />
              </template>
              <el-empty v-else description="暂无物流信息" :image-size="80" />
            </el-dialog>
          </div>
        </el-main>
      </el-container>
    </el-container>
    <el-footer class="footer-content">版权所有 ©[xb商城]，保留所有权利。</el-footer>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Loading, Location } from '@element-plus/icons-vue'
import BuyerNavigation from '@/moon/buyer_navigation.vue'
import BuyerHead from '@/moon/buyer_head.vue'
import BuyerTheme from '@/moon/buyer_theme'

defineOptions({ name: 'BuyerLogisticsManage' })

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const getHeaders = () => {
  const token = localStorage.getItem('buyer_access_token')
  return token ? { 'Access-Token': token } : {}
}

const isOwner = ref(false)
const storeList = ref<{ id: number; mall_name: string }[]>([])
const selectedMallId = ref<number | null>(null)

function decodeTokenPayload(token: string): Record<string, any> | null {
  try {
    const parts = token.split('.')
    if (parts.length < 2) return null
    const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(payload))
  } catch {
    return null
  }
}

async function loadStoreList() {
  const token = localStorage.getItem('buyer_access_token')
  if (!token) return
  const payload = decodeTokenPayload(token)
  if (!payload || String(payload.station) !== '1') return
  isOwner.value = true
  try {
    const form = new FormData()
    form.append('token', token)
    const res = await Axios.post('/get_mall_name', form)
    if (res.data?.mall_name?.length) {
      storeList.value = res.data.mall_name
      selectedMallId.value = storeList.value[0].id
    }
  } catch (e) {
    console.error('加载店铺列表失败', e)
  }
}

function mallParam(): Record<string, any> {
  const p: Record<string, any> = {}
  if (isOwner.value && selectedMallId.value != null) {
    p.mall_id = selectedMallId.value
  }
  return p
}

function onStoreChange() {
  page.value = 1
  fetchList()
}

interface LogisticsItem {
  id: number
  order_no: string
  mall_id: number
  express_company: string
  tracking_number: string
  sender_name: string
  sender_phone: string
  sender_address: string
  status: string
  created_at: string
  receiver_name: string
  receiver_phone: string
  receiver_addr: string
  total_amount: number | null
  order_status: string
}

const keyword = ref('')
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const list = ref<LogisticsItem[]>([])

function orderStatusText(s: string) {
  const map: Record<string, string> = {
    pending: '待支付', paid: '已支付', shipped: '已发货',
    received: '已收货', closed: '已关闭', refunded: '已退款',
  }
  return map[s] || s
}

function orderStatusType(s: string) {
  const map: Record<string, string> = {
    shipped: '', paid: 'warning', received: 'success',
    closed: 'info', refunded: 'danger',
  }
  return map[s] || 'info'
}

function doSearch() {
  page.value = 1
  fetchList()
}

async function fetchList() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: page.value,
      page_size: pageSize.value,
      ...mallParam(),
    }
    if (keyword.value) params.keyword = keyword.value
    const res = await Axios.get('/seller/logistics/list', { params, headers: getHeaders() })
    if (res.data?.success) {
      list.value = res.data.data || []
      total.value = res.data.total || 0
    } else if (res.data?.msg) {
      ElMessage.error(res.data.msg)
    }
  } catch {
    ElMessage.error('请求失败')
  } finally {
    loading.value = false
  }
}

// ── 详情弹窗 ──
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailData = ref<any>(null)

async function viewDetail(item: LogisticsItem) {
  detailVisible.value = true
  detailLoading.value = true
  detailData.value = null
  try {
    const res = await Axios.get('/seller/logistics/detail', {
      params: { order_no: item.order_no },
      headers: getHeaders(),
    })
    if (res.data?.success) {
      detailData.value = res.data.data
    } else {
      ElMessage.warning(res.data?.msg || '暂无物流信息')
    }
  } catch {
    ElMessage.error('查询物流详情失败')
  } finally {
    detailLoading.value = false
  }
}

onMounted(async () => {
  new BuyerTheme().initTheme()
  await loadStoreList()
  fetchList()
})
</script>

<style scoped>
.el-header {
  border-bottom: 1px solid #514d4d;
  padding-bottom: 10px;
  margin-bottom: 10px;
}
.logistics-container {
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
.lm-store-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 10px 16px;
  background: var(--el-bg-color);
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.lm-store-label {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}
.lm-search {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.lm-loading, .lm-empty {
  text-align: center;
  padding: 60px 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
.lm-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  transition: box-shadow 0.2s;
}
.lm-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.lm-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.lm-card-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.lm-order-no {
  font-weight: 500;
  font-size: 14px;
  font-family: monospace;
  color: var(--el-text-color-primary);
}
.lm-time {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}
.lm-card-body {
  font-size: 13px;
}
.lm-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
}
.lm-label {
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
  min-width: 80px;
}
.lm-val {
  color: var(--el-text-color-primary);
  text-align: right;
}
.lm-val--mono {
  font-family: monospace;
}
.lm-val--price {
  font-weight: 600;
  color: var(--el-color-danger);
}
.lm-card-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--el-border-color-lighter);
}
.lm-pagination {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}
.lm-detail-info {
  background: var(--el-fill-color-extra-light);
  border-radius: 10px;
  padding: 16px;
}
.footer-content {
  text-align: center;
  color: darkgray;
}
</style>
