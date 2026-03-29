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
              <el-tag size="small" type="success">进行中</el-tag>
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
            </div>
            <div class="card-actions">
              <el-button type="primary" size="small" @click="openJoinDialog(item)">加入活动</el-button>
              <el-button size="small" plain @click="openLeaveDialog(item)">退出活动</el-button>
            </div>
          </div>
        </el-card>
      </div>
      <div class="pager">
        <el-pagination :page-size="pageSize" layout="total, prev, pager, next" :total="total" :current-page="page" @current-change="loadList" />
      </div>
    </div>

    <!-- 加入活动对话框 -->
    <el-dialog v-model="joinVisible" title="选择商品加入活动" width="600px" destroy-on-close>
      <el-alert v-if="currentActivity" :title="`即将加入: ${currentActivity.name}`" type="info" :closable="false" style="margin-bottom: 16px" />
      <el-form label-width="100px">
        <div v-for="(p, i) in joinProducts" :key="i" class="product-row">
          <el-form-item :label="`商品 ${i + 1}`">
            <div style="display: flex; gap: 8px; align-items: center; width: 100%">
              <el-input-number v-model="p.shopping_id" :min="1" placeholder="商品ID" size="default" style="width: 120px" />
              <el-input-number v-model="p.activity_price" :min="0.01" :precision="2" placeholder="活动价" size="default" style="width: 130px" />
              <el-input-number v-model="p.activity_stock" :min="1" placeholder="活动库存" size="default" style="width: 130px" />
              <el-button v-if="joinProducts.length > 1" type="danger" size="small" circle :icon="Minus" @click="joinProducts.splice(i, 1)" />
            </div>
          </el-form-item>
        </div>
        <el-form-item>
          <el-button type="primary" size="small" plain :icon="Plus" @click="joinProducts.push({ shopping_id: null, activity_price: null, activity_stock: null })">添加商品</el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="joinVisible = false">取消</el-button>
        <el-button type="primary" :loading="joinSubmitting" @click="submitJoin">确认加入</el-button>
      </template>
    </el-dialog>

    <!-- 退出活动对话框 -->
    <el-dialog v-model="leaveVisible" title="退出平台活动" width="480px">
      <el-alert v-if="currentActivity" :title="`即将退出: ${currentActivity.name}`" type="warning" :closable="false" style="margin-bottom: 16px" />
      <el-form label-width="100px">
        <el-form-item label="退出方式">
          <el-radio-group v-model="leaveMode">
            <el-radio value="all">退出全部商品</el-radio>
            <el-radio value="partial">退出指定商品</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="leaveMode === 'partial'" label="商品ID列表">
          <el-input v-model="leaveIdsInput" placeholder="用英文逗号分隔，如: 101,102,103" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="leaveVisible = false">取消</el-button>
        <el-button type="warning" :loading="leaveSubmitting" @click="submitLeave">确认退出</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Plus, Refresh, Minus } from '@element-plus/icons-vue'

defineOptions({ name: 'BuyerJoinActivity' })

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

const currentActivity = ref<any>(null)

const joinVisible = ref(false)
const joinSubmitting = ref(false)
const joinProducts = ref<any[]>([{ shopping_id: null, activity_price: null, activity_stock: null }])

const leaveVisible = ref(false)
const leaveSubmitting = ref(false)
const leaveMode = ref('all')
const leaveIdsInput = ref('')

function actTypeLabel(t: string) {
  return { flash_sale: '秒杀', full_reduction: '满减', discount: '折扣', group_buy: '拼团' }[t] || t
}
function actTypeTag(t: string) {
  return { flash_sale: 'danger', full_reduction: 'warning', discount: 'success', group_buy: '' }[t] || 'info'
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

async function loadList(p: number) {
  loading.value = true
  page.value = p
  try {
    const { data } = await API.get('/buyer_activity/joinable', { params: { page: p, page_size: pageSize.value, ...mallParam() }, headers })
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

function openJoinDialog(activity: any) {
  currentActivity.value = activity
  joinProducts.value = [{ shopping_id: null, activity_price: null, activity_stock: null }]
  joinVisible.value = true
}

async function submitJoin() {
  const valid = joinProducts.value.filter((p: any) => p.shopping_id)
  if (valid.length === 0) return ElMessage.warning('请至少添加一个商品')

  joinSubmitting.value = true
  try {
    const body = {
      activity_id: currentActivity.value.id,
      products: valid.map((p: any) => ({
        mall_id: 0,
        shopping_id: p.shopping_id,
        activity_price: p.activity_price,
        activity_stock: p.activity_stock,
      })),
    }
    const { data } = await API.post('/buyer_activity/join', body, { params: mallParam(), headers })
    if (data.success) {
      ElMessage.success(data.msg)
      joinVisible.value = false
    } else {
      ElMessage.error(data.msg)
    }
  } catch {
    ElMessage.error('加入活动失败')
  } finally {
    joinSubmitting.value = false
  }
}

function openLeaveDialog(activity: any) {
  currentActivity.value = activity
  leaveMode.value = 'all'
  leaveIdsInput.value = ''
  leaveVisible.value = true
}

async function submitLeave() {
  leaveSubmitting.value = true
  try {
    const body: any = { activity_id: currentActivity.value.id }
    if (leaveMode.value === 'partial') {
      const ids = leaveIdsInput.value.split(',').map((s: string) => parseInt(s.trim())).filter((n: number) => !isNaN(n))
      if (ids.length === 0) return ElMessage.warning('请输入要退出的商品ID')
      body.shopping_ids = ids
    }
    const { data } = await API.post('/buyer_activity/leave', body, { params: mallParam(), headers })
    if (data.success) {
      ElMessage.success(data.msg)
      leaveVisible.value = false
    } else {
      ElMessage.error(data.msg)
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

.activity-card {
  border-radius: 10px;
  transition: transform 0.2s;
}
.activity-card:hover { transform: translateY(-2px); }

.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title-row { display: flex; align-items: center; gap: 8px; }
.card-name { font-size: 15px; font-weight: 600; }

.card-body { display: flex; flex-direction: column; gap: 12px; }
.card-info { display: flex; flex-direction: column; gap: 6px; }
.info-row { font-size: 13px; color: var(--el-text-color-regular); display: flex; }
.info-row .label { color: var(--el-text-color-secondary); min-width: 72px; flex-shrink: 0; }
.rules-text { color: var(--el-color-primary); font-weight: 500; }

.card-actions { display: flex; gap: 8px; margin-top: 4px; }

.product-row { margin-bottom: 4px; }

@media (max-width: 768px) {
  .activity-cards { grid-template-columns: 1fr; }
}
</style>
