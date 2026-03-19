<template>
    <div class="appeal-container">
        <div class="filter-bar">
            <el-input
                v-model="select"
                style="width: 240px; margin-right: 12px;"
                placeholder="搜索申诉内容/申请人"
                :prefix-icon="Search"
                @keyup.enter="getAppealList(1)"
                clearable
            />
            <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px;"
                       @change="getAppealList(1)">
                <el-option label="待处理" value="pending" />
                <el-option label="已通过" value="approved" />
                <el-option label="已驳回" value="rejected" />
            </el-select>
        </div>

        <div v-if="loading" class="loading-container">
            <el-skeleton :rows="5" animated />
        </div>
        <div v-else-if="appeal_list.length === 0" class="empty-container">
            <el-empty description="暂无申诉记录" />
        </div>
        <div v-else>
            <el-card v-for="item in appeal_list" :key="item.appeal_id" class="appeal-card"
                     :class="{ 'appeal-pending': item.status === 'pending', 'appeal-approved': item.status === 'approved', 'appeal-rejected': item.status === 'rejected' }">
                <div class="appeal-card-content">
                    <div class="appeal-img">
                        <el-image
                            v-if="item.img"
                            :src="item.img"
                            style="width: 80px; height: 80px; border-radius: 8px;"
                            fit="cover"
                            :preview-src-list="[item.img]"
                            preview-teleported
                        />
                        <div v-else class="no-img">暂无图片</div>
                    </div>
                    <div class="appeal-info">
                        <div class="appeal-name">
                            <el-tag :type="item.status === 'pending' ? 'warning' : item.status === 'approved' ? 'success' : 'danger'"
                                    size="small" effect="dark" style="margin-right: 8px;">
                                {{ item.status_text }}
                            </el-tag>
                            {{ item.commodity_name }}
                        </div>
                        <div class="appeal-meta">
                            <span>店铺：{{ item.mall_name }}（ID:{{ item.mall_id }}）</span>
                            <span>商品ID：{{ item.shopping_id }}</span>
                            <span>申请人：{{ item.applicant }}</span>
                        </div>
                        <div class="appeal-violation" v-if="item.violation_reason">
                            <el-icon style="margin-right: 4px;"><WarningFilled /></el-icon>
                            违规原因：{{ item.violation_reason }}
                        </div>
                        <div class="appeal-reason">
                            <el-icon style="margin-right: 4px;"><ChatDotSquare /></el-icon>
                            申诉理由：{{ item.reason }}
                        </div>
                        <div class="appeal-time">
                            申诉时间：{{ item.appeal_time }}
                            <template v-if="item.handle_time">
                                &nbsp;|&nbsp; 处理时间：{{ item.handle_time }}（{{ item.handler }}）
                            </template>
                        </div>
                        <div class="appeal-remark" v-if="item.remark">
                            处理备注：{{ item.remark }}
                        </div>
                    </div>
                    <div class="appeal-actions" v-if="item.status === 'pending'">
                        <el-button type="success" size="small" plain @click="handleAppeal(item, 'approve')">
                            通过申诉
                        </el-button>
                        <el-button type="danger" size="small" plain @click="handleAppeal(item, 'reject')">
                            驳回申诉
                        </el-button>
                    </div>
                </div>
            </el-card>

            <div style="display: flex; justify-content: center; margin-top: 20px;">
                <el-pagination
                    :page-size="pageSize"
                    layout="total, prev, pager, next"
                    :total="total"
                    :current-page="currentPage"
                    @current-change="getAppealList"
                />
            </div>
        </div>

        <!-- 处理申诉对话框 -->
        <el-dialog v-model="handleDialogVisible" :title="handleAction === 'approve' ? '通过申诉' : '驳回申诉'" width="500px">
            <el-form :model="handleForm" label-width="80px">
                <el-form-item label="商品名称">
                    <el-text>{{ currentAppeal?.commodity_name }}</el-text>
                </el-form-item>
                <el-form-item label="申诉理由">
                    <el-text>{{ currentAppeal?.reason }}</el-text>
                </el-form-item>
                <el-form-item label="处理备注">
                    <el-input
                        v-model="handleForm.remark"
                        type="textarea"
                        :rows="3"
                        :placeholder="handleAction === 'approve' ? '可选，通过申诉的备注说明' : '请填写驳回原因'"
                        maxlength="200"
                        show-word-limit
                    />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="handleDialogVisible = false">取消</el-button>
                <el-button :type="handleAction === 'approve' ? 'success' : 'danger'"
                           :loading="handleLoading"
                           @click="submitHandle">
                    {{ handleAction === 'approve' ? '确认通过' : '确认驳回' }}
                </el-button>
            </template>
        </el-dialog>
    </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Search, WarningFilled, ChatDotSquare } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

defineOptions({
    name: 'CommodityAppealManage',
    components: { Search, WarningFilled, ChatDotSquare }
})

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const token = localStorage.getItem('admin_access_token')

interface AppealItem {
    appeal_id: string
    mall_id: number
    shopping_id: number
    commodity_name: string
    mall_name: string
    reason: string
    applicant: string
    status: string
    status_text: string
    appeal_time: string
    handle_time: string
    handler: string
    remark: string
    violation_reason: string
    img: string
}

const appeal_list = ref<AppealItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const select = ref('')
const statusFilter = ref('')
const loading = ref(false)

const handleDialogVisible = ref(false)
const handleAction = ref<'approve' | 'reject'>('approve')
const handleLoading = ref(false)
const currentAppeal = ref<AppealItem | null>(null)
const handleForm = ref({ remark: '' })

async function getAppealList(page: number) {
    loading.value = true
    currentPage.value = page
    try {
        const params: any = { page, page_size: pageSize.value }
        if (select.value) params.select_data = select.value
        if (statusFilter.value) params.status = statusFilter.value

        const res = await Axios.get('/manage_commodity_appeal_list', {
            params,
            headers: { 'access-token': token }
        })
        if (res.status === 200 && res.data.current) {
            appeal_list.value = res.data.appeal_list
            total.value = res.data.total
        } else {
            ElMessage.warning(res.data.msg || '获取数据失败')
            appeal_list.value = []
            total.value = 0
        }
    } catch (e) {
        ElMessage.error('请求失败')
    } finally {
        loading.value = false
    }
}

function handleAppeal(item: AppealItem, action: 'approve' | 'reject') {
    currentAppeal.value = item
    handleAction.value = action
    handleForm.value.remark = ''
    handleDialogVisible.value = true
}

async function submitHandle() {
    if (!currentAppeal.value) return
    if (handleAction.value === 'reject' && !handleForm.value.remark.trim()) {
        ElMessage.warning('驳回时请填写驳回原因')
        return
    }

    handleLoading.value = true
    try {
        const formData = new FormData()
        formData.append('token', token || '')
        formData.append('appeal_id', currentAppeal.value.appeal_id)
        formData.append('action', handleAction.value)
        if (handleForm.value.remark.trim()) {
            formData.append('remark', handleForm.value.remark.trim())
        }

        const res = await Axios.post('/manage_commodity_appeal_handle', formData)
        if (res.data.current) {
            ElMessage.success(res.data.msg)
            handleDialogVisible.value = false
            await getAppealList(currentPage.value)
        } else {
            ElMessage.error(res.data.msg)
        }
    } catch (e) {
        ElMessage.error('操作失败')
    } finally {
        handleLoading.value = false
    }
}

onMounted(() => {
    getAppealList(1)
})
</script>
<style scoped>
.appeal-container {
    padding: 10px;
}

.filter-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24px;
}

:deep(.el-input__wrapper) {
    border-radius: 20px;
}

.loading-container {
    padding: 40px;
}

.empty-container {
    padding: 60px 0;
}

.appeal-card {
    margin-bottom: 16px;
    border-radius: 12px;
    transition: all 0.3s ease;
}

.appeal-card:hover {
    transform: translateY(-2px);
}

.appeal-pending {
    border: 1px solid rgba(230, 162, 60, 0.3);
}

.appeal-pending:hover {
    box-shadow: 0 4px 16px rgba(230, 162, 60, 0.2);
}

.appeal-approved {
    border: 1px solid rgba(103, 194, 58, 0.2);
}

.appeal-approved:hover {
    box-shadow: 0 4px 16px rgba(103, 194, 58, 0.15);
}

.appeal-rejected {
    border: 1px solid rgba(245, 108, 108, 0.2);
}

.appeal-rejected:hover {
    box-shadow: 0 4px 16px rgba(245, 108, 108, 0.15);
}

.appeal-card-content {
    display: flex;
    align-items: flex-start;
    gap: 20px;
}

.appeal-img .no-img {
    width: 80px;
    height: 80px;
    border-radius: 8px;
    background: var(--el-fill-color-light);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: var(--el-text-color-placeholder);
}

.appeal-info {
    flex: 1;
    min-width: 0;
}

.appeal-name {
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
}

.appeal-meta {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    display: flex;
    gap: 20px;
    margin-bottom: 6px;
    flex-wrap: wrap;
}

.appeal-violation {
    font-size: 13px;
    color: var(--el-color-danger);
    display: flex;
    align-items: center;
    margin-bottom: 4px;
}

.appeal-reason {
    font-size: 13px;
    color: var(--el-color-primary);
    display: flex;
    align-items: center;
    margin-bottom: 4px;
}

.appeal-time {
    font-size: 12px;
    color: var(--el-text-color-placeholder);
    margin-bottom: 4px;
}

.appeal-remark {
    font-size: 13px;
    color: var(--el-text-color-regular);
    padding: 6px 10px;
    background: var(--el-fill-color-lighter);
    border-radius: 6px;
    margin-top: 4px;
}

.appeal-actions {
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
}
</style>
