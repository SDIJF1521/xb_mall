<template>
    <div class="commodity-list-container">
        <div class="filter-bar">
            <el-input
                v-model="select"
                style="width: 240px; border-radius: 20px;"
                placeholder="搜索商品名称"
                :prefix-icon="Search"
                @keyup.enter="getCommodityList(1)"
                clearable
            />
            <el-select v-model="statusFilter" placeholder="商品状态" style="width: 220px; margin-left: 12px;" clearable @change="getCommodityList(1)">
                <el-option label="全部" value="" />
                <el-option label="待审核" value="auditing" />
                <el-option label="上架" value="on_sale" />
                <el-option label="已下架" value="off_shelf" />
                <el-option label="违规" value="violation" />
                <el-option label="店铺关闭异常" value="store_closed" />
                <el-option label="审核未通过" value="rejected" />
            </el-select>
            <el-input
                v-model="mallIdFilter"
                style="width: 160px; margin-left: 12px;"
                placeholder="店铺ID筛选"
                @keyup.enter="getCommodityList(1)"
                clearable
                type="number"
            />
        </div>

        <div v-if="loading" class="loading-container">
            <el-skeleton :rows="5" animated />
        </div>
        <div v-else-if="commodity_list.length === 0" class="empty-container">
            <el-empty description="暂无商品数据" />
        </div>
        <div v-else>
            <el-table :data="commodity_list" stripe style="width: 100%" :header-cell-style="{background: 'var(--el-fill-color-light)'}" >
                <el-table-column prop="shopping_id" label="商品ID" width="90" align="center" />
                <el-table-column label="商品图片" width="90" align="center">
                    <template #default="scope">
                        <el-image
                            v-if="scope.row.img"
                            :src="scope.row.img"
                            style="width: 50px; height: 50px; border-radius: 6px;"
                            fit="cover"
                            :preview-src-list="[scope.row.img]"
                            preview-teleported
                        />
                        <span v-else>-</span>
                    </template>
                </el-table-column>
                <el-table-column prop="name" label="商品名称" min-width="160" show-overflow-tooltip />
                <el-table-column prop="mall_name" label="所属店铺" min-width="120" show-overflow-tooltip />
                <el-table-column prop="mall_id" label="店铺ID" width="80" align="center" />
                <el-table-column label="状态" width="150" align="center" show-overflow-tooltip>
                    <template #default="scope">
                        <el-tag :type="getStatusType(scope.row.audit)" size="small" effect="dark">
                            {{ scope.row.audit_text }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="time" label="提交时间" min-width="160" show-overflow-tooltip />
                <el-table-column label="操作" width="180" align="center" fixed="right">
                    <template #default="scope">
                        <el-button v-if="scope.row.audit === 1" type="warning" size="small" plain @click="handleViolation(scope.row)">
                            标记违规
                        </el-button>
                        <el-button v-if="scope.row.audit === 1" type="danger" size="small" plain @click="handleOffShelf(scope.row)">
                            强制下架
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>
            <div style="display: flex; justify-content: center; margin-top: 20px;">
                <el-pagination
                    :page-size="pageSize"
                    layout="total, prev, pager, next"
                    :total="total"
                    :current-page="currentPage"
                    @current-change="getCommodityList"
                />
            </div>
        </div>

        <!-- 违规标记对话框 -->
        <el-dialog v-model="violationDialogVisible" title="标记商品违规" width="500px">
            <el-form label-width="80px">
                <el-form-item label="商品名称">
                    <span>{{ violationTarget.name }}</span>
                </el-form-item>
                <el-form-item label="违规原因">
                    <el-input v-model="violationReason" type="textarea" :rows="4" placeholder="请输入违规原因" />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="violationDialogVisible = false">取消</el-button>
                <el-button type="danger" @click="submitViolation" :loading="submitLoading">确认标记</el-button>
            </template>
        </el-dialog>
    </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

defineOptions({ name: 'CommodityList' })

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const token = localStorage.getItem('admin_access_token')

interface CommodityItem {
    shopping_id: number
    name: string
    mall_id: number
    mall_name: string
    audit: number
    audit_text: string
    time: string
    info: string
    img: string
    types: string[]
}

const commodity_list = ref<CommodityItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const select = ref('')
const statusFilter = ref('')
const mallIdFilter = ref('')
const loading = ref(false)

const violationDialogVisible = ref(false)
const violationReason = ref('')
const violationTarget = ref<CommodityItem>({} as CommodityItem)
const submitLoading = ref(false)

function getStatusType(audit: number) {
    // 0=待审核 1=上架 3=已下架 4=违规 5=店铺关闭异常 其他=审核未通过
    const map: Record<number, string> = { 0: 'info', 1: 'success', 3: 'warning', 4: 'danger', 5: 'danger' }
    return map[audit] || 'danger'
}

async function getCommodityList(page: number) {
    loading.value = true
    currentPage.value = page
    try {
        const params: any = { page, page_size: pageSize.value }
        if (select.value) params.select_data = select.value
        if (statusFilter.value) params.status = statusFilter.value
        if (mallIdFilter.value) params.mall_id = parseInt(mallIdFilter.value)

        const res = await Axios.get('/manage_commodity_list', {
            params,
            headers: { 'access-token': token }
        })
        if (res.status === 200 && res.data.current) {
            commodity_list.value = res.data.commodity_list
            total.value = res.data.total
        } else {
            ElMessage.warning(res.data.msg || '获取数据失败')
            commodity_list.value = []
            total.value = 0
        }
    } catch (e) {
        ElMessage.error('请求失败')
    } finally {
        loading.value = false
    }
}

function handleViolation(row: CommodityItem) {
    violationTarget.value = row
    violationReason.value = ''
    violationDialogVisible.value = true
}

async function submitViolation() {
    if (!violationReason.value.trim()) {
        ElMessage.warning('请输入违规原因')
        return
    }
    submitLoading.value = true
    try {
        const formData = new FormData()
        formData.append('token', token || '')
        formData.append('mall_id', violationTarget.value.mall_id.toString())
        formData.append('shopping_id', violationTarget.value.shopping_id.toString())
        formData.append('reason', violationReason.value)

        const res = await Axios.post('/manage_commodity_violation_add', formData)
        if (res.data.current) {
            ElMessage.success(res.data.msg)
            violationDialogVisible.value = false
            await getCommodityList(currentPage.value)
        } else {
            ElMessage.error(res.data.msg)
        }
    } catch (e) {
        ElMessage.error('操作失败')
    } finally {
        submitLoading.value = false
    }
}

async function handleOffShelf(row: CommodityItem) {
    try {
        await ElMessageBox.confirm(`确定要强制下架商品「${row.name}」吗？`, '确认操作', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
        })
        const formData = new FormData()
        formData.append('token', token || '')
        formData.append('mall_id', row.mall_id.toString())
        formData.append('shopping_id', row.shopping_id.toString())
        formData.append('reason', '平台强制下架')

        const res = await Axios.post('/manage_commodity_violation_add', formData)
        if (res.data.current) {
            ElMessage.success('已强制下架')
            await getCommodityList(currentPage.value)
        } else {
            ElMessage.error(res.data.msg)
        }
    } catch (e) {
        // 用户取消
    }
}

onMounted(() => {
    getCommodityList(1)
})
</script>
<style scoped>
.commodity-list-container {
    padding: 10px;
}

.filter-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 8px;
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

:deep(.el-table) {
    border-radius: 8px;
    overflow: hidden;
}
</style>
