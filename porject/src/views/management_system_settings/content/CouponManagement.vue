<template>
  <div class="coupon-manage">
    <!-- 顶部操作栏 -->
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">创建优惠券</el-button>
      <div class="toolbar-right">
        <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 130px" @change="loadList(1)">
          <el-option label="草稿" value="draft" />
          <el-option label="已上线" value="active" />
          <el-option label="已暂停" value="paused" />
          <el-option label="已过期" value="expired" />
        </el-select>
        <el-select v-model="filterIssuer" placeholder="发布方" clearable style="width: 130px; margin-left: 8px" @change="loadList(1)">
          <el-option label="平台" value="platform" />
          <el-option label="商家" value="merchant" />
        </el-select>
        <el-button :icon="Refresh" circle style="margin-left: 8px" @click="loadList(page)" />
      </div>
    </div>

    <!-- 列表 -->
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
        <el-table-column label="发布方" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.issuer_type === 'platform' ? 'danger' : 'warning'">
              {{ row.issuer_type === 'platform' ? '平台' : '商家' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="优惠" width="120" align="center">
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
        <el-table-column label="范围" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ scopeLabel(row.platform_scope) }}</el-tag>
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
    <el-dialog v-model="createVisible" title="创建优惠券" width="640px" destroy-on-close>
      <el-form :model="form" label-width="120px" ref="formRef">
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
          <el-radio-group v-model="form.scope">
            <el-radio value="all_mall">全商城</el-radio>
            <el-radio value="store">指定店铺</el-radio>
            <el-radio value="product">指定商品</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="平台控制">
          <el-radio-group v-model="form.platform_scope">
            <el-radio value="all">全商城可用</el-radio>
            <el-radio value="merchant_choice">允许商家自选</el-radio>
          </el-radio-group>
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
          <el-descriptions-item label="发布方">{{ detail.issuer_type === 'platform' ? '平台' : '商家' }}</el-descriptions-item>
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
          <el-descriptions-item label="平台范围">{{ scopeLabel(detail.platform_scope) }}</el-descriptions-item>
          <el-descriptions-item v-if="detail.description" label="说明" :span="2">{{ detail.description }}</el-descriptions-item>
          <el-descriptions-item label="创建人">{{ detail.created_by || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ detail.created_at?.slice(0, 16) }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'

defineOptions({ name: 'CouponManagement' })

const API = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const token = localStorage.getItem('admin_access_token')
const headers = { 'access-token': token || '' }

const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const filterStatus = ref('')
const filterIssuer = ref('')

const createVisible = ref(false)
const submitting = ref(false)
const form = ref<any>({
  name: '', coupon_type: 'full_reduction', min_order_amount: 0,
  discount_value: 10, max_discount: null, total_count: 0,
  per_user_limit: 1, scope: 'all_mall', platform_scope: 'all',
  timeRange: null, description: '',
})

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
function scopeLabel(s: string) {
  return { all: '全商城', merchant_choice: '商家自选' }[s] || s
}

async function loadList(p: number) {
  loading.value = true
  page.value = p
  try {
    const params: Record<string, any> = { page: p, page_size: pageSize.value }
    if (filterStatus.value) params.status = filterStatus.value
    if (filterIssuer.value) params.issuer_type = filterIssuer.value
    const { data } = await API.get('/manage_coupon/list', { params, headers })
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
    per_user_limit: 1, scope: 'all_mall', platform_scope: 'all',
    timeRange: null, description: '',
  }
  createVisible.value = true
}

async function submitCreate() {
  const f = form.value
  if (!f.name?.trim()) return ElMessage.warning('请输入优惠券名称')
  if (!f.timeRange || f.timeRange.length < 2) return ElMessage.warning('请选择有效期')

  submitting.value = true
  try {
    const body = {
      name: f.name, coupon_type: f.coupon_type,
      discount_value: f.discount_value, min_order_amount: f.min_order_amount,
      start_time: f.timeRange[0], end_time: f.timeRange[1],
      scope: f.scope, platform_scope: f.platform_scope,
      max_discount: f.max_discount, total_count: f.total_count,
      per_user_limit: f.per_user_limit, description: f.description,
    }
    const { data } = await API.post('/manage_coupon/create', body, { headers })
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
    const { data } = await API.post('/manage_coupon/status', { coupon_id: id, status }, { headers })
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
    const { data } = await API.post('/manage_coupon/delete', { coupon_id: id }, { headers })
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
    const { data } = await API.get('/manage_coupon/detail', { params: { coupon_id: id }, headers })
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
</style>
