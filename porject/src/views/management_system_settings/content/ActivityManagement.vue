<template>
  <div class="activity-manage">
    <!-- 顶部操作栏 -->
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
        <el-select v-model="filterIssuer" placeholder="发起方" clearable style="width: 120px; margin-left: 8px" @change="loadList(1)">
          <el-option label="平台" value="platform" />
          <el-option label="商家" value="merchant" />
        </el-select>
        <el-button :icon="Refresh" circle style="margin-left: 8px" @click="loadList(page)" />
      </div>
    </div>

    <!-- 列表 -->
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
        <el-table-column label="发起方" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.issuer_type === 'platform' ? 'danger' : 'warning'">
              {{ row.issuer_type === 'platform' ? '平台' : '商家' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="商家参与" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.platform_scope === 'all' ? '全商城' : '自选加入' }}</el-tag>
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
    <el-dialog v-model="createVisible" title="创建活动" width="680px" destroy-on-close>
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

        <!-- 秒杀规则 -->
        <template v-if="form.activity_type === 'flash_sale'">
          <el-form-item label="折扣率">
            <el-input-number v-model="form.rules.discount_rate" :min="0.01" :max="0.99" :precision="2" style="width: 200px" />
            <span style="margin-left: 8px; color: var(--el-text-color-placeholder)">如 0.5 = 五折</span>
          </el-form-item>
        </template>

        <!-- 满减规则 -->
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

        <!-- 折扣规则 -->
        <template v-if="form.activity_type === 'discount'">
          <el-form-item label="折扣率">
            <el-input-number v-model="form.rules.discount_rate" :min="0.01" :max="0.99" :precision="2" style="width: 200px" />
            <span style="margin-left: 8px; color: var(--el-text-color-placeholder)">如 0.85 = 85折</span>
          </el-form-item>
        </template>

        <!-- 拼团规则 -->
        <template v-if="form.activity_type === 'group_buy'">
          <el-form-item label="最少成团人数">
            <el-input-number v-model="form.rules.min_group_size" :min="2" style="width: 200px" />
          </el-form-item>
          <el-form-item label="折扣率">
            <el-input-number v-model="form.rules.discount_rate" :min="0.01" :max="0.99" :precision="2" style="width: 200px" />
          </el-form-item>
        </template>

        <el-form-item label="商家参与方式">
          <el-radio-group v-model="form.platform_scope">
            <el-radio value="all">全商城自动参与</el-radio>
            <el-radio value="merchant_choice">商家自选加入</el-radio>
          </el-radio-group>
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
          <el-descriptions-item label="发起方">{{ detail.issuer_type === 'platform' ? '平台' : '商家' }}</el-descriptions-item>
          <el-descriptions-item label="活动时间" :span="2">{{ detail.start_time?.slice(0, 16) }} 至 {{ detail.end_time?.slice(0, 16) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTag(detail.status)" size="small">{{ statusLabel(detail.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="商家参与">{{ detail.platform_scope === 'all' ? '全商城' : '自选加入' }}</el-descriptions-item>
          <el-descriptions-item label="规则" :span="2">
            <pre style="margin: 0; white-space: pre-wrap; font-size: 13px">{{ JSON.stringify(detail.rules, null, 2) }}</pre>
          </el-descriptions-item>
          <el-descriptions-item v-if="detail.description" label="说明" :span="2">{{ detail.description }}</el-descriptions-item>
          <el-descriptions-item label="创建人">{{ detail.created_by || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ detail.created_at?.slice(0, 16) }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="detail.products?.length" style="margin-top: 20px">
          <h4 style="margin-bottom: 10px">活动商品 ({{ detail.products.length }})</h4>
          <el-table :data="detail.products" size="small" stripe>
            <el-table-column prop="mall_id" label="店铺ID" width="80" />
            <el-table-column prop="shopping_id" label="商品ID" width="80" />
            <el-table-column label="活动价" width="100">
              <template #default="{ row }">{{ row.activity_price ? `¥${row.activity_price}` : '-' }}</template>
            </el-table-column>
            <el-table-column label="活动库存" width="100">
              <template #default="{ row }">{{ row.activity_stock ?? '不限' }}</template>
            </el-table-column>
            <el-table-column prop="sold_count" label="已售" width="80" />
            <el-table-column label="加入方" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="row.joined_by === 'platform' ? 'danger' : 'warning'">
                  {{ row.joined_by === 'platform' ? '平台' : '商家' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div v-if="detail.coupons?.length" style="margin-top: 20px">
          <h4 style="margin-bottom: 10px">关联优惠券 ({{ detail.coupons.length }})</h4>
          <el-table :data="detail.coupons" size="small" stripe>
            <el-table-column prop="coupon_no" label="编号" width="190" />
            <el-table-column prop="name" label="名称" />
            <el-table-column label="类型" width="100">
              <template #default="{ row }">{{ actTypeLabel(row.coupon_type) }}</template>
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
import { Plus, Refresh, Minus } from '@element-plus/icons-vue'

defineOptions({ name: 'ActivityManagement' })

const API = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const token = localStorage.getItem('admin_access_token')
const headers = { 'access-token': token || '' }

const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const filterType = ref('')
const filterStatus = ref('')
const filterIssuer = ref('')

const createVisible = ref(false)
const submitting = ref(false)

function defaultRules(type: string) {
  if (type === 'flash_sale') return { discount_rate: 0.5 }
  if (type === 'full_reduction') return { thresholds: [{ min_amount: 100, reduction: 10 }] }
  if (type === 'discount') return { discount_rate: 0.85 }
  if (type === 'group_buy') return { min_group_size: 2, discount_rate: 0.8 }
  return {}
}

const form = ref<any>({
  name: '', activity_type: 'flash_sale',
  rules: defaultRules('flash_sale'),
  platform_scope: 'all', timeRange: null, description: '',
})

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

function onTypeChange(type: string) {
  form.value.rules = defaultRules(type)
}

async function loadList(p: number) {
  loading.value = true
  page.value = p
  try {
    const params: Record<string, any> = { page: p, page_size: pageSize.value }
    if (filterType.value) params.activity_type = filterType.value
    if (filterStatus.value) params.status = filterStatus.value
    if (filterIssuer.value) params.issuer_type = filterIssuer.value
    const { data } = await API.get('/manage_activity/list', { params, headers })
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
    platform_scope: 'all', timeRange: null, description: '',
  }
  createVisible.value = true
}

async function submitCreate() {
  const f = form.value
  if (!f.name?.trim()) return ElMessage.warning('请输入活动名称')
  if (!f.timeRange || f.timeRange.length < 2) return ElMessage.warning('请选择活动时间')

  submitting.value = true
  try {
    const body = {
      name: f.name, activity_type: f.activity_type,
      start_time: f.timeRange[0], end_time: f.timeRange[1],
      rules: f.rules, platform_scope: f.platform_scope,
      description: f.description,
    }
    const { data } = await API.post('/manage_activity/create', body, { headers })
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
    const { data } = await API.post('/manage_activity/status', { activity_id: id, status }, { headers })
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
    const { data } = await API.post('/manage_activity/delete', { activity_id: id }, { headers })
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
    const { data } = await API.get('/manage_activity/detail', { params: { activity_id: id }, headers })
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
</style>
