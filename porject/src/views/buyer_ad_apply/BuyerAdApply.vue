<template>
  <el-container>
    <el-container>
      <BuyerNavigation />
      <el-container>
        <el-header>
          <BuyerHead />
        </el-header>
        <el-main>
          <div class="ad-apply-container">
            <h2 class="page-title">广告投放管理</h2>
            <p class="page-subtitle">向平台申请轮播图广告投放，提升商品曝光度</p>

            <el-tabs v-model="activeTab" type="border-card" class="main-tabs">
              <!-- 发起申请 -->
              <el-tab-pane label="发起投放申请" name="create">
                <el-form :model="form" label-width="100px" style="max-width: 600px; margin: 20px auto;">
                  <el-form-item label="选择商品" required>
                    <el-select
                      v-model="form.shopping_id"
                      filterable
                      remote
                      :remote-method="searchCommodity"
                      placeholder="搜索并选择要推广的商品"
                      style="width: 100%;"
                      :loading="commodityLoading"
                    >
                      <el-option
                        v-for="item in commodityOptions"
                        :key="item.id"
                        :label="item.name"
                        :value="item.id"
                      />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="广告标题" required>
                    <el-input v-model="form.title" placeholder="输入广告标题（展示在轮播图上）" maxlength="100" show-word-limit />
                  </el-form-item>
                  <el-form-item label="申请说明">
                    <el-input v-model="form.description" type="textarea" :rows="3" placeholder="简要说明投放目的（可选）" />
                  </el-form-item>
                  <el-form-item label="投放天数">
                    <el-input-number v-model="form.duration_days" :min="1" :max="90" />
                    <span style="margin-left: 8px; color: var(--el-text-color-secondary);">天</span>
                  </el-form-item>
                  <el-form-item label="广告图片">
                    <el-upload
                      ref="uploadRef"
                      :auto-upload="false"
                      :limit="1"
                      accept="image/*"
                      list-type="picture-card"
                      :on-change="handleFileChange"
                      :on-remove="handleFileRemove"
                    >
                      <el-icon><Plus /></el-icon>
                      <template #tip>
                        <div class="el-upload__tip">推荐尺寸 1200x400，不上传则使用商品主图</div>
                      </template>
                    </el-upload>
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" @click="submitApply" :loading="submitLoading">提交申请</el-button>
                  </el-form-item>
                </el-form>
              </el-tab-pane>

              <!-- 我的申请 -->
              <el-tab-pane label="我的申请记录" name="list">
                <div class="toolbar">
                  <el-select v-model="listStatusFilter" placeholder="筛选状态" clearable style="width: 140px;" @change="loadApplyList(1)">
                    <el-option label="待审核" value="pending" />
                    <el-option label="已通过" value="approved" />
                    <el-option label="已驳回" value="rejected" />
                  </el-select>
                  <el-button :icon="Refresh" circle style="margin-left: 8px;" @click="loadApplyList(listPage)" />
                </div>

                <div v-if="listLoading" class="loading-box"><el-skeleton :rows="4" animated /></div>
                <div v-else-if="applyList.length === 0" class="empty-box"><el-empty description="暂无投放申请" /></div>
                <div v-else>
                  <el-table :data="applyList" stripe>
                    <el-table-column prop="id" label="ID" width="60" align="center" />
                    <el-table-column prop="title" label="标题" min-width="140" show-overflow-tooltip />
                    <el-table-column prop="commodity_name" label="商品" min-width="130" show-overflow-tooltip />
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
                    <el-table-column label="备注" min-width="160" show-overflow-tooltip>
                      <template #default="{ row }">
                        <span v-if="row.status === 'rejected'" style="color: var(--el-color-danger);">{{ row.reject_reason }}</span>
                        <span v-else-if="row.status === 'approved'" style="color: var(--el-color-success);">审核通过</span>
                        <span v-else style="color: var(--el-text-color-placeholder);">等待平台审核</span>
                      </template>
                    </el-table-column>
                  </el-table>
                  <div class="pager">
                    <el-pagination
                      :page-size="listPageSize"
                      layout="total, prev, pager, next"
                      :total="listTotal"
                      :current-page="listPage"
                      @current-change="loadApplyList"
                    />
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-main>
      </el-container>
    </el-container>
    <el-footer class="footer-content">版权所有 ©[xb商城]，保留所有权利。</el-footer>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import BuyerHead from '@/moon/buyer_head.vue'
import BuyerNavigation from '@/moon/buyer_navigation.vue'
import BuyerTheme from '@/moon/buyer_theme'

defineOptions({ name: 'BuyerAdApply' })

const route = useRoute()
const storeId = ref(Number(route.params.id) || 0)
const token = ref(localStorage.getItem('buyer_access_token') || '')
const API = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

const activeTab = ref('create')

// ─── 发起申请 ─────────────────────────────────────────────────────────────

interface CommodityOption { id: number; name: string }

const form = ref({ shopping_id: null as number | null, title: '', description: '', duration_days: 7 })
const adFile = ref<File | null>(null)
const submitLoading = ref(false)
const commodityOptions = ref<CommodityOption[]>([])
const commodityLoading = ref(false)
const uploadRef = ref()

async function loadCommodityOptions(query?: string) {
  commodityLoading.value = true
  try {
    const params: Record<string, unknown> = { stroe_id: storeId.value, page: 1 }
    if (query && query.trim()) params.select = query.trim()
    const { data } = await API.get('/buyer_get_commoidt', {
      params,
      headers: { 'access-token': token.value }
    })
    if (data.success && Array.isArray(data.data)) {
      commodityOptions.value = data.data.map((c: any) => ({ id: c.id, name: c.name }))
    }
  } catch { /* ignore */ } finally {
    commodityLoading.value = false
  }
}

function searchCommodity(query: string) {
  loadCommodityOptions(query)
}

function handleFileChange(file: any) { adFile.value = file.raw }
function handleFileRemove() { adFile.value = null }

async function submitApply() {
  if (!form.value.shopping_id) { ElMessage.warning('请选择商品'); return }
  if (!form.value.title.trim()) { ElMessage.warning('请输入广告标题'); return }
  submitLoading.value = true
  try {
    const fd = new FormData()
    fd.append('token', token.value)
    fd.append('stroe_id', storeId.value.toString())
    fd.append('shopping_id', form.value.shopping_id.toString())
    fd.append('title', form.value.title.trim())
    fd.append('description', form.value.description)
    fd.append('duration_days', form.value.duration_days.toString())
    if (adFile.value) fd.append('ad_img', adFile.value)

    const { data } = await API.post('/buyer_ad_apply', fd)
    if (data.current) {
      ElMessage.success(data.msg)
      form.value = { shopping_id: null, title: '', description: '', duration_days: 7 }
      adFile.value = null
      uploadRef.value?.clearFiles()
      activeTab.value = 'list'
      loadApplyList(1)
    } else {
      ElMessage.error(data.msg)
    }
  } catch {
    ElMessage.error('提交失败')
  } finally {
    submitLoading.value = false
  }
}

// ─── 申请列表 ─────────────────────────────────────────────────────────────

interface ApplyItem {
  id: number; shopping_id: number; title: string; description: string | null
  img_path: string | null; duration_days: number; status: string
  reject_reason: string | null; apply_time: string | null; review_time: string | null
  commodity_name: string
}

const applyList = ref<ApplyItem[]>([])
const listTotal = ref(0)
const listPage = ref(1)
const listPageSize = ref(10)
const listStatusFilter = ref('')
const listLoading = ref(false)

async function loadApplyList(page: number) {
  listLoading.value = true
  listPage.value = page
  try {
    const params: Record<string, unknown> = { stroe_id: storeId.value, page, page_size: listPageSize.value }
    if (listStatusFilter.value) params.status = listStatusFilter.value
    const { data } = await API.get('/buyer_ad_apply_list', {
      params,
      headers: { 'access-token': token.value }
    })
    if (data.current) {
      applyList.value = data.data
      listTotal.value = data.total
    }
  } catch {
    ElMessage.error('获取申请列表失败')
  } finally {
    listLoading.value = false
  }
}

function statusLabel(s: string) {
  return { pending: '待审核', approved: '已通过', rejected: '已驳回' }[s] || s
}
function statusTag(s: string) {
  return ({ pending: 'warning', approved: 'success', rejected: 'danger' } as Record<string, string>)[s] || 'info'
}

onMounted(() => {
  new BuyerTheme().initTheme()
  loadCommodityOptions()
  loadApplyList(1)
})
</script>

<style lang="scss" scoped>
.footer-content { text-align: center; color: darkgray; }
.el-header { border-bottom: 1px solid #514d4d; padding-bottom: 10px; margin-bottom: 10px; }

.ad-apply-container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}

.page-title {
  text-align: center;
  font-size: 24px;
  margin-bottom: 4px;
}

.page-subtitle {
  text-align: center;
  color: var(--el-text-color-secondary);
  margin-bottom: 24px;
}

.main-tabs {
  border-radius: 8px;
}

.toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}

.loading-box { padding: 40px; }
.empty-box { padding: 60px 0; }
.pager { display: flex; justify-content: center; margin-top: 20px; }

:deep(.el-table) { border-radius: 8px; overflow: hidden; }
</style>
