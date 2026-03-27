<template>
  <div class="ad-setting">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 轮播图管理 -->
      <el-tab-pane label="轮播图管理" name="banner">
        <div class="toolbar">
          <el-select v-model="bannerFilter" placeholder="筛选状态" clearable style="width: 140px;" @change="loadBanners(1)">
            <el-option label="已启用" :value="1" />
            <el-option label="已禁用" :value="0" />
          </el-select>
          <el-button :icon="Refresh" circle @click="loadBanners(bannerPage)" />
        </div>

        <div v-if="bannerLoading" class="loading-box"><el-skeleton :rows="4" animated /></div>
        <div v-else-if="bannerList.length === 0" class="empty-box"><el-empty description="暂无轮播图广告" /></div>
        <div v-else>
          <el-table :data="bannerList" stripe :header-cell-style="{ background: 'var(--el-fill-color-light)' }">
            <el-table-column label="预览" width="120" align="center">
              <template #default="{ row }">
                <el-image
                  v-if="row.img"
                  :src="toBase64Src(row.img)"
                  style="width: 90px; height: 50px; border-radius: 4px;"
                  fit="cover"
                  :preview-src-list="[toBase64Src(row.img)]"
                />
                <span v-else style="color: var(--el-text-color-placeholder);">无图</span>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" min-width="140" show-overflow-tooltip />
            <el-table-column prop="mall_name" label="店铺" min-width="120" show-overflow-tooltip />
            <el-table-column prop="commodity_name" label="商品" min-width="120" show-overflow-tooltip />
            <el-table-column label="排序" width="120" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.sort_order"
                  :min="0"
                  :max="9999"
                  size="small"
                  controls-position="right"
                  @change="updateBanner(row.id, row.sort_order, undefined)"
                />
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-switch
                  v-model="row.is_active"
                  :active-value="1"
                  :inactive-value="0"
                  @change="updateBanner(row.id, undefined, row.is_active)"
                />
              </template>
            </el-table-column>
            <el-table-column label="投放时间" width="190" align="center">
              <template #default="{ row }">
                <div style="font-size: 12px; line-height: 1.6;">
                  <div>{{ row.start_time?.slice(0, 16) }}</div>
                  <div style="color: var(--el-text-color-placeholder);">至 {{ row.end_time?.slice(0, 16) }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" align="center" fixed="right">
              <template #default="{ row }">
                <el-popconfirm title="确定删除该轮播广告？" @confirm="deleteBanner(row.id)">
                  <template #reference>
                    <el-button type="danger" size="small" plain :icon="Delete" />
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
          <div class="pager">
            <el-pagination
              :page-size="bannerPageSize"
              layout="total, prev, pager, next"
              :total="bannerTotal"
              :current-page="bannerPage"
              @current-change="loadBanners"
            />
          </div>
        </div>
      </el-tab-pane>

      <!-- 投放申请审核 -->
      <el-tab-pane label="投放申请审核" name="apply">
        <div class="toolbar">
          <el-input
            v-model="applySearch"
            style="width: 220px;"
            placeholder="搜索标题/店铺名"
            :prefix-icon="Search"
            clearable
            @keyup.enter="loadApplies(1)"
          />
          <el-select v-model="applyStatusFilter" placeholder="筛选状态" clearable style="width: 140px; margin-left: 8px;" @change="loadApplies(1)">
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已驳回" value="rejected" />
          </el-select>
          <el-button :icon="Refresh" circle style="margin-left: 8px;" @click="loadApplies(applyPage)" />
        </div>

        <div v-if="applyLoading" class="loading-box"><el-skeleton :rows="4" animated /></div>
        <div v-else-if="applyList.length === 0" class="empty-box"><el-empty description="暂无投放申请" /></div>
        <div v-else>
          <el-table :data="applyList" stripe :header-cell-style="{ background: 'var(--el-fill-color-light)' }">
            <el-table-column prop="id" label="ID" width="70" align="center" />
            <el-table-column label="商品图" width="90" align="center">
              <template #default="{ row }">
                <el-image
                  v-if="row.img"
                  :src="toBase64Src(row.img)"
                  style="width: 60px; height: 40px; border-radius: 4px;"
                  fit="cover"
                />
                <span v-else style="color: var(--el-text-color-placeholder);">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="广告标题" min-width="130" show-overflow-tooltip />
            <el-table-column prop="mall_name" label="店铺" min-width="110" show-overflow-tooltip />
            <el-table-column prop="commodity_name" label="商品" min-width="110" show-overflow-tooltip />
            <el-table-column prop="duration_days" label="天数" width="70" align="center">
              <template #default="{ row }">{{ row.duration_days }}天</template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="statusTag(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="apply_time" label="申请时间" width="160" align="center">
              <template #default="{ row }">{{ row.apply_time?.slice(0, 16) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="160" align="center" fixed="right">
              <template #default="{ row }">
                <template v-if="row.status === 'pending'">
                  <el-button type="success" size="small" plain @click="handleApprove(row)">通过</el-button>
                  <el-button type="danger" size="small" plain @click="openRejectDialog(row)">驳回</el-button>
                </template>
                <template v-else>
                  <el-button size="small" plain @click="showApplyDetail(row)">详情</el-button>
                </template>
              </template>
            </el-table-column>
          </el-table>
          <div class="pager">
            <el-pagination
              :page-size="applyPageSize"
              layout="total, prev, pager, next"
              :total="applyTotal"
              :current-page="applyPage"
              @current-change="loadApplies"
            />
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 驳回对话框 -->
    <el-dialog v-model="rejectDialogVisible" title="驳回投放申请" width="460px">
      <el-form label-width="80px">
        <el-form-item label="申请标题">
          <el-input :model-value="rejectTarget?.title" disabled />
        </el-form-item>
        <el-form-item label="驳回原因">
          <el-input v-model="rejectReason" type="textarea" :rows="3" placeholder="请输入驳回原因" maxlength="200" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="submitReject" :loading="rejectLoading">确认驳回</el-button>
      </template>
    </el-dialog>

    <!-- 申请详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="申请详情" width="520px">
      <template v-if="detailTarget">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="广告标题" :span="2">{{ detailTarget.title }}</el-descriptions-item>
          <el-descriptions-item label="店铺">{{ detailTarget.mall_name }}</el-descriptions-item>
          <el-descriptions-item label="商品">{{ detailTarget.commodity_name }}</el-descriptions-item>
          <el-descriptions-item label="投放天数">{{ detailTarget.duration_days }}天</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTag(detailTarget.status)" size="small">{{ statusLabel(detailTarget.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="申请时间">{{ detailTarget.apply_time?.slice(0, 16) }}</el-descriptions-item>
          <el-descriptions-item label="审核时间">{{ detailTarget.review_time?.slice(0, 16) || '-' }}</el-descriptions-item>
          <el-descriptions-item label="申请说明" :span="2">{{ detailTarget.description || '无' }}</el-descriptions-item>
          <el-descriptions-item v-if="detailTarget.reject_reason" label="驳回原因" :span="2">
            <span style="color: var(--el-color-danger);">{{ detailTarget.reject_reason }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Delete } from '@element-plus/icons-vue'

defineOptions({ name: 'AdSetting' })

const API = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const token = localStorage.getItem('admin_access_token')
const headers = { 'access-token': token || '' }

const activeTab = ref('banner')

// ─── 轮播图管理 ───────────────────────────────────────────────────────────

interface BannerItem {
  id: number; apply_id: number | null; mall_id: number; shopping_id: number
  title: string; img: string; sort_order: number; is_active: number
  start_time: string | null; end_time: string | null; created_at: string | null
  mall_name: string; commodity_name: string
}

const bannerList = ref<BannerItem[]>([])
const bannerTotal = ref(0)
const bannerPage = ref(1)
const bannerPageSize = ref(20)
const bannerFilter = ref<number | undefined>(undefined)
const bannerLoading = ref(false)

async function loadBanners(page: number) {
  bannerLoading.value = true
  bannerPage.value = page
  try {
    const params: Record<string, unknown> = { page, page_size: bannerPageSize.value }
    if (bannerFilter.value !== undefined && bannerFilter.value !== null) params.is_active = bannerFilter.value
    const { data } = await API.get('/manage_ad_banner_list', { params, headers })
    if (data.current) {
      bannerList.value = data.data
      bannerTotal.value = data.total
    } else {
      ElMessage.warning(data.msg)
    }
  } catch {
    ElMessage.error('获取轮播图列表失败')
  } finally {
    bannerLoading.value = false
  }
}

async function updateBanner(id: number, sort?: number, active?: number) {
  try {
    const body: Record<string, unknown> = { banner_id: id }
    if (sort !== undefined) body.sort_order = sort
    if (active !== undefined) body.is_active = active
    const { data } = await API.patch('/manage_ad_banner_update', body, { headers })
    if (data.current) {
      ElMessage.success(data.msg)
    } else {
      ElMessage.error(data.msg)
      loadBanners(bannerPage.value)
    }
  } catch {
    ElMessage.error('更新失败')
  }
}

async function deleteBanner(id: number) {
  try {
    const { data } = await API.delete('/manage_ad_banner_delete', { data: { banner_id: id }, headers })
    if (data.current) {
      ElMessage.success(data.msg)
      loadBanners(bannerPage.value)
    } else {
      ElMessage.error(data.msg)
    }
  } catch {
    ElMessage.error('删除失败')
  }
}

// ─── 投放申请审核 ─────────────────────────────────────────────────────────

interface ApplyItem {
  id: number; mall_id: number; shopping_id: number; title: string
  description: string | null; img: string; duration_days: number
  status: string; reject_reason: string | null; apply_time: string | null
  review_time: string | null; reviewer: string | null; mall_name: string
  commodity_name: string
}

const applyList = ref<ApplyItem[]>([])
const applyTotal = ref(0)
const applyPage = ref(1)
const applyPageSize = ref(20)
const applySearch = ref('')
const applyStatusFilter = ref('')
const applyLoading = ref(false)

async function loadApplies(page: number) {
  applyLoading.value = true
  applyPage.value = page
  try {
    const params: Record<string, unknown> = { page, page_size: applyPageSize.value }
    if (applySearch.value) params.select_data = applySearch.value
    if (applyStatusFilter.value) params.status = applyStatusFilter.value
    const { data } = await API.get('/manage_ad_apply_list', { params, headers })
    if (data.current) {
      applyList.value = data.data
      applyTotal.value = data.total
    } else {
      ElMessage.warning(data.msg)
    }
  } catch {
    ElMessage.error('获取申请列表失败')
  } finally {
    applyLoading.value = false
  }
}

async function handleApprove(row: ApplyItem) {
  try {
    await ElMessageBox.confirm(
      `确认通过「${row.title}」的投放申请？通过后将自动在轮播图上线。`,
      '审批确认',
      { confirmButtonText: '通过', cancelButtonText: '取消', type: 'success' }
    )
    const { data } = await API.post('/manage_ad_apply_approve', { apply_id: row.id }, { headers })
    if (data.current) {
      ElMessage.success(data.msg)
      loadApplies(applyPage.value)
      loadBanners(1)
    } else {
      ElMessage.error(data.msg)
    }
  } catch {
    // cancelled
  }
}

const rejectDialogVisible = ref(false)
const rejectTarget = ref<ApplyItem | null>(null)
const rejectReason = ref('')
const rejectLoading = ref(false)

function openRejectDialog(row: ApplyItem) {
  rejectTarget.value = row
  rejectReason.value = ''
  rejectDialogVisible.value = true
}

async function submitReject() {
  if (!rejectReason.value.trim()) {
    ElMessage.warning('请输入驳回原因')
    return
  }
  rejectLoading.value = true
  try {
    const { data } = await API.post('/manage_ad_apply_reject', {
      apply_id: rejectTarget.value!.id,
      reason: rejectReason.value.trim()
    }, { headers })
    if (data.current) {
      ElMessage.success(data.msg)
      rejectDialogVisible.value = false
      loadApplies(applyPage.value)
    } else {
      ElMessage.error(data.msg)
    }
  } catch {
    ElMessage.error('操作失败')
  } finally {
    rejectLoading.value = false
  }
}

const detailDialogVisible = ref(false)
const detailTarget = ref<ApplyItem | null>(null)

function showApplyDetail(row: ApplyItem) {
  detailTarget.value = row
  detailDialogVisible.value = true
}

// ─── 通用 ─────────────────────────────────────────────────────────────────

function toBase64Src(b64: string): string {
  if (!b64) return ''
  if (b64.startsWith('data:')) return b64
  return `data:image/jpeg;base64,${b64}`
}

function statusLabel(s: string) {
  return { pending: '待审核', approved: '已通过', rejected: '已驳回' }[s] || s
}

function statusTag(s: string) {
  return ({ pending: 'warning', approved: 'success', rejected: 'danger' } as Record<string, string>)[s] || 'info'
}

onMounted(() => {
  loadBanners(1)
  loadApplies(1)
})
</script>

<style scoped>
.ad-setting {
  min-height: 400px;
}

.toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}

.loading-box {
  padding: 40px;
}

.empty-box {
  padding: 60px 0;
}

.pager {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-tabs__content) {
  padding: 16px 8px;
}
</style>
