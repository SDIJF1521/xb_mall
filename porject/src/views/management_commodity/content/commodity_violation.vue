<template>
    <div class="violation-container">
        <div class="filter-bar">
            <el-input
                v-model="select"
                style="width: 240px;"
                placeholder="搜索违规商品"
                :prefix-icon="Search"
                @keyup.enter="getViolationList(1)"
                clearable
            />
        </div>

        <div v-if="loading" class="loading-container">
            <el-skeleton :rows="5" animated />
        </div>
        <div v-else-if="violation_list.length === 0" class="empty-container">
            <el-empty description="暂无违规商品" />
        </div>
        <div v-else>
            <el-card v-for="item in violation_list" :key="`${item.mall_id}-${item.shopping_id}`" class="violation-card">
                <div class="violation-card-content">
                    <div class="violation-img">
                        <el-image
                            v-if="item.img"
                            :src="item.img"
                            style="width: 80px; height: 80px; border-radius: 8px;"
                            fit="cover"
                            :preview-src-list="[item.img]"
                        />
                        <div v-else class="no-img">暂无图片</div>
                    </div>
                    <div class="violation-info">
                        <div class="violation-name">
                            <el-tag type="danger" size="small" effect="dark" style="margin-right: 8px;">违规</el-tag>
                            {{ item.name }}
                        </div>
                        <div class="violation-meta">
                            <span>店铺：{{ item.mall_name }}（ID:{{ item.mall_id }}）</span>
                            <span>商品ID：{{ item.shopping_id }}</span>
                        </div>
                        <div class="violation-reason" v-if="item.reason">
                            <el-icon style="margin-right: 4px;"><WarningFilled /></el-icon>
                            违规原因：{{ item.reason }}
                        </div>
                        <div class="violation-time" v-if="item.violation_time">
                            标记时间：{{ item.violation_time }}
                        </div>
                    </div>
                    <div class="violation-actions">
                        <el-button type="success" size="small" plain @click="handleRemove(item)">
                            取消违规
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
                    @current-change="getViolationList"
                />
            </div>
        </div>
    </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Search, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

defineOptions({
    name: 'CommodityViolation',
    components: { Search, WarningFilled }
})

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const token = localStorage.getItem('admin_access_token')

interface ViolationItem {
    shopping_id: number
    name: string
    mall_id: number
    mall_name: string
    time: string
    info: string
    reason: string
    violation_time: string
    img: string
}

const violation_list = ref<ViolationItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const select = ref('')
const loading = ref(false)

async function getViolationList(page: number) {
    loading.value = true
    currentPage.value = page
    try {
        const params: any = { page, page_size: pageSize.value }
        if (select.value) params.select_data = select.value

        const res = await Axios.get('/manage_commodity_violation_list', {
            params,
            headers: { 'access-token': token }
        })
        if (res.status === 200 && res.data.current) {
            violation_list.value = res.data.violation_list
            total.value = res.data.total
        } else {
            ElMessage.warning(res.data.msg || '获取数据失败')
            violation_list.value = []
            total.value = 0
        }
    } catch (e) {
        ElMessage.error('请求失败')
    } finally {
        loading.value = false
    }
}

async function handleRemove(item: ViolationItem) {
    try {
        await ElMessageBox.confirm(`确定要取消商品「${item.name}」的违规标记吗？取消后商品将恢复为已下架状态。`, '确认操作', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
        })
        const formData = new FormData()
        formData.append('token', token || '')
        formData.append('mall_id', item.mall_id.toString())
        formData.append('shopping_id', item.shopping_id.toString())

        const res = await Axios.post('/manage_commodity_violation_remove', formData)
        if (res.data.current) {
            ElMessage.success(res.data.msg)
            await getViolationList(currentPage.value)
        } else {
            ElMessage.error(res.data.msg)
        }
    } catch (e) {
        // 用户取消
    }
}

onMounted(() => {
    getViolationList(1)
})
</script>
<style scoped>
.violation-container {
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

.violation-card {
    margin-bottom: 16px;
    border-radius: 12px;
    transition: all 0.3s ease;
    border: 1px solid rgba(245, 108, 108, 0.15);
}

.violation-card:hover {
    box-shadow: 0 4px 16px rgba(245, 108, 108, 0.2);
    transform: translateY(-2px);
}

.violation-card-content {
    display: flex;
    align-items: center;
    gap: 20px;
}

.violation-img .no-img {
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

.violation-info {
    flex: 1;
    min-width: 0;
}

.violation-name {
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
}

.violation-meta {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    display: flex;
    gap: 20px;
    margin-bottom: 6px;
}

.violation-reason {
    font-size: 13px;
    color: var(--el-color-danger);
    display: flex;
    align-items: center;
    margin-bottom: 4px;
}

.violation-time {
    font-size: 12px;
    color: var(--el-text-color-placeholder);
}

.violation-actions {
    flex-shrink: 0;
}
</style>
