<template>
    <div class="classify-container">
        <div class="filter-bar">
            <el-input
                v-model="select"
                style="width: 240px;"
                placeholder="搜索分类名称"
                :prefix-icon="Search"
                @keyup.enter="getClassifyList(1)"
                clearable
            />
            <el-button type="primary" style="margin-left: 12px;" @click="showAddDialog">
                <el-icon style="margin-right: 4px;"><Plus /></el-icon>
                新增分类
            </el-button>
        </div>

        <div v-if="loading" class="loading-container">
            <el-skeleton :rows="5" animated />
        </div>
        <div v-else-if="classify_list.length === 0" class="empty-container">
            <el-empty description="暂无分类数据" />
        </div>
        <div v-else>
            <el-table :data="classify_list" stripe style="width: 100%" :header-cell-style="{background: 'var(--el-fill-color-light)'}">
                <el-table-column prop="id" label="分类ID" width="100" align="center" />
                <el-table-column prop="name" label="分类名称" min-width="200" show-overflow-tooltip />
                <el-table-column prop="mall_name" label="所属" min-width="160" show-overflow-tooltip>
                    <template #default="scope">
                        <el-tag v-if="scope.row.store_id === 0" type="primary" size="small" effect="plain">平台分类</el-tag>
                        <span v-else>{{ scope.row.mall_name }}（ID:{{ scope.row.store_id }}）</span>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="200" align="center" fixed="right">
                    <template #default="scope">
                        <el-button type="primary" size="small" plain @click="showEditDialog(scope.row)">编辑</el-button>
                        <el-button type="danger" size="small" plain @click="handleDelete(scope.row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <div style="display: flex; justify-content: center; margin-top: 20px;">
                <el-pagination
                    :page-size="pageSize"
                    layout="total, prev, pager, next"
                    :total="total"
                    :current-page="currentPage"
                    @current-change="getClassifyList"
                />
            </div>
        </div>

        <!-- 新增/编辑对话框 -->
        <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑分类' : '新增分类'" width="420px">
            <el-form label-width="80px">
                <el-form-item label="分类名称">
                    <el-input v-model="formName" placeholder="请输入分类名称" maxlength="20" show-word-limit />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="dialogVisible = false">取消</el-button>
                <el-button type="primary" @click="submitForm" :loading="submitLoading">确认</el-button>
            </template>
        </el-dialog>
    </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Search, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

defineOptions({
    name: 'CommodityClassify',
    components: { Search, Plus }
})

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const token = localStorage.getItem('admin_access_token')

interface ClassifyItem {
    id: number
    name: string
    store_id: number
    mall_name: string
}

const classify_list = ref<ClassifyItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const select = ref('')
const loading = ref(false)

const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(0)
const formName = ref('')
const submitLoading = ref(false)

async function getClassifyList(page: number) {
    loading.value = true
    currentPage.value = page
    try {
        const params: any = { page, page_size: pageSize.value }
        if (select.value) params.select_data = select.value

        const res = await Axios.get('/manage_commodity_classify_list', {
            params,
            headers: { 'access-token': token }
        })
        if (res.status === 200 && res.data.current) {
            classify_list.value = res.data.classify_list
            total.value = res.data.total
        } else {
            ElMessage.warning(res.data.msg || '获取数据失败')
            classify_list.value = []
            total.value = 0
        }
    } catch (e) {
        ElMessage.error('请求失败')
    } finally {
        loading.value = false
    }
}

function showAddDialog() {
    isEdit.value = false
    formName.value = ''
    editId.value = 0
    dialogVisible.value = true
}

function showEditDialog(row: ClassifyItem) {
    isEdit.value = true
    formName.value = row.name
    editId.value = row.id
    dialogVisible.value = true
}

async function submitForm() {
    if (!formName.value.trim()) {
        ElMessage.warning('请输入分类名称')
        return
    }
    submitLoading.value = true
    try {
        const formData = new FormData()
        formData.append('token', token || '')
        formData.append('name', formName.value.trim())

        if (isEdit.value) {
            formData.append('classify_id', editId.value.toString())
            const res = await Axios.post('/manage_commodity_classify_edit', formData)
            if (res.data.current) {
                ElMessage.success(res.data.msg)
                dialogVisible.value = false
                await getClassifyList(currentPage.value)
            } else {
                ElMessage.error(res.data.msg)
            }
        } else {
            const res = await Axios.post('/manage_commodity_classify_add', formData)
            if (res.data.current) {
                ElMessage.success(res.data.msg)
                dialogVisible.value = false
                await getClassifyList(1)
            } else {
                ElMessage.error(res.data.msg)
            }
        }
    } catch (e) {
        ElMessage.error('操作失败')
    } finally {
        submitLoading.value = false
    }
}

async function handleDelete(row: ClassifyItem) {
    try {
        await ElMessageBox.confirm(`确定要删除分类「${row.name}」吗？`, '确认删除', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
        })
        const formData = new FormData()
        formData.append('token', token || '')
        formData.append('classify_id', row.id.toString())

        const res = await Axios.post('/manage_commodity_classify_delete', formData)
        if (res.data.current) {
            ElMessage.success(res.data.msg)
            await getClassifyList(currentPage.value)
        } else {
            ElMessage.error(res.data.msg)
        }
    } catch (e) {
        // 用户取消
    }
}

onMounted(() => {
    getClassifyList(1)
})
</script>
<style scoped>
.classify-container {
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
