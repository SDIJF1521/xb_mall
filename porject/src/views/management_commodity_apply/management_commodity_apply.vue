<template>
    <el-dialog
     v-model="dialogVisible"
     :title="title"
    >
       <component ref="currentComponent" :is="mod" v-if="dialogVisible" @reject="handleReject" @cancel="handleCancel" @pass="handlePass" />
       <template #footer>
         <div class="dialog-footer">
           <el-button
             type="danger"
             @click="handleCancel"
             size="large"
             :icon="Close"
             class="cancel-btn"
           >
             取消
           </el-button>
           <!-- 拒绝审核按钮 -->
           <el-button
             v-if="mod === 'CommodityRejectAudit'"
             type="primary"
             @click="triggerReject"
             size="large"
             :icon="Check"
             class="confirm-btn reject-btn"
             :loading="submitting"
           >
             确认拒绝
           </el-button>
           <!-- 通过审核按钮 -->
           <el-button
             v-if="mod === 'CommodityPassAudit'"
             type="success"
             @click="triggerPass"
             size="large"
             :icon="Check"
             class="confirm-btn pass-btn"
             :loading="submitting"
           >
             确认通过
           </el-button>
         </div>
       </template>
    </el-dialog>
    <el-container>
        <ManagementNavigation/>
        <el-main class="commodity-detail-main">
            <div v-if="loading" class="loading-container">
                <el-skeleton :rows="8" animated />
            </div>
            <div v-else-if="commodityInfo" class="detail-container">
                <!-- 返回按钮 -->
                <div class="action-bar">
                    <el-button type="primary" :icon="ArrowLeft" @click="goBack" class="back-button">
                        返回列表
                    </el-button>
                    <el-tag type="warning" size="large" class="status-tag">
                        <el-icon><Clock /></el-icon>
                        待审核
                    </el-tag>
                </div>

                <!-- 商品基本信息卡片 -->
                <el-card class="detail-card" shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <div class="header-left">
                                <el-icon class="header-icon"><Goods /></el-icon>
                                <h2>商品审核详情</h2>
                            </div>
                        </div>
                    </template>
                    <el-descriptions title="商品基本信息" :column="2" border class="commodity-descriptions">
                        <el-descriptions-item label="商品名称" :span="2">
                            <div class="name-wrapper">
                                <span class="commodity-name">{{ commodityInfo.name }}</span>
                            </div>
                        </el-descriptions-item>
                        <el-descriptions-item label="商品ID">
                            <el-tag type="info">{{ shopping_id }}</el-tag>
                        </el-descriptions-item>
                        <el-descriptions-item label="店铺ID">
                            <el-tag type="info">{{ mall_id }}</el-tag>
                        </el-descriptions-item>
                        <el-descriptions-item label="商品分类" v-if="commodityInfo.classify">
                            <el-tag type="success">{{ commodityInfo.classify }}</el-tag>
                        </el-descriptions-item>
                        <el-descriptions-item label="商品类型" v-if="commodityInfo.classify_categorize">
                            <el-tag>{{ commodityInfo.classify_categorize }}</el-tag>
                        </el-descriptions-item>
                        <el-descriptions-item label="商品标签" v-if="commodityInfo.types">
                            <el-tag v-for="item in commodityInfo.types">{{ item }}</el-tag>
                        </el-descriptions-item>
                        <el-descriptions-item label="创建时间">
                            <div class="time-wrapper">
                                <el-icon><Calendar /></el-icon>
                                <span>{{ commodityInfo.time }}</span>
                            </div>
                        </el-descriptions-item>
                        <el-descriptions-item label="商品描述" :span="2">
                            <div class="commodity-info">
                                <div v-if="commodityInfo.info" class="info-content">
                                    {{ commodityInfo.info }}
                                </div>
                                <el-empty v-else description="暂无描述" :image-size="60" />
                            </div>
                        </el-descriptions-item>
                    </el-descriptions>
                </el-card>

                <!-- 商品图片卡片 -->
                <el-card class="detail-card image-card" shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <div class="header-left">
                                <el-icon class="header-icon"><Picture /></el-icon>
                                <h3>商品图片</h3>
                                <el-tag v-if="commodityInfo.img_list && commodityInfo.img_list.length > 0" type="info" size="small" class="count-tag">
                                    {{ commodityInfo.img_list.length }} 张
                                </el-tag>
                            </div>
                        </div>
                    </template>
                    <div v-if="commodityInfo.img_list && commodityInfo.img_list.length > 0" class="image-gallery">
                        <div 
                            v-for="(img, index) in commodityInfo.img_list" 
                            :key="index" 
                            class="image-item"
                        >
                            <el-image
                                :src="`data:image/jpeg;base64,${img}`"
                                :preview-src-list="previewImageList"
                                :initial-index="index"
                                fit="cover"
                                class="gallery-image"
                                :preview-teleported="true"
                                lazy
                            />
                            <div class="image-index">{{ index + 1 }}</div>
                        </div>
                    </div>
                    <el-empty v-else description="暂无图片" :image-size="100" />
                </el-card>

                <!-- 商品规格卡片 -->
                <el-card class="detail-card specification-card" shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <div class="header-left">
                                <el-icon class="header-icon"><List /></el-icon>
                                <h3>商品规格</h3>
                                <el-tag v-if="commodityInfo.specification_list && commodityInfo.specification_list.length > 0" type="info" size="small" class="count-tag">
                                    {{ commodityInfo.specification_list.length }} 种规格
                                </el-tag>
                            </div>
                        </div>
                    </template>
                    <div v-if="commodityInfo.specification_list && commodityInfo.specification_list.length > 0" class="specification-list">
                        <el-table 
                            :data="specificationTableData" 
                            border 
                            style="width: 100%"
                            :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: '600' }"
                        >
                            <el-table-column type="index" label="序号" width="80" align="center" />
                            <el-table-column prop="specification" label="规格名称" min-width="200">
                                <template #default="scope">
                                    <el-tag>{{ scope.row.specification }}</el-tag>
                                </template>
                            </el-table-column>
                            <el-table-column prop="price" label="价格" width="180" align="center">
                                <template #default="scope">
                                    <span class="price-text">¥{{ scope.row.price.toFixed(2) }}</span>
                                </template>
                            </el-table-column>
                            <el-table-column prop="stock" label="库存" width="150" align="center">
                                <template #default="scope">
                                    <el-tag :type="scope.row.stock > 0 ? 'success' : 'danger'" size="large">
                                        {{ scope.row.stock }}
                                    </el-tag>
                                </template>
                            </el-table-column>
                        </el-table>
                    </div>
                    <el-empty v-else description="暂无规格信息" :image-size="100" />
                </el-card>

                <!-- 审核操作卡片 -->
                <el-card class="detail-card action-card" shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <div class="header-left">
                                <el-icon class="header-icon"><EditPen /></el-icon>
                                <h3>审核操作</h3>
                            </div>
                        </div>
                    </template>
                    <div class="action-buttons">
                        <el-button 
                            type="success" 
                            size="large" 
                            :icon="Check"
                            class="audit-button approve-button"
                            @click="passAudit"
                        >
                            通过审核
                        </el-button>
                        <el-button 
                            type="danger" 
                            size="large" 
                            :icon="Close"
                            class="audit-button reject-button"
                            @click="rejectAudit"
                        >
                            拒绝审核
                        </el-button>
                    </div>
                </el-card>
            </div>
            <el-empty v-else description="暂无商品信息" :image-size="200" />
        </el-main>
        <el-footer class="footer-content">
            <p>版权所有 © [小白的商城]，保留所有权利。</p>
        </el-footer>
    </el-container>
</template>
<script setup lang="ts">
import {ref,onMounted,computed} from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios';
import { ElMessage } from 'element-plus'
import { ArrowLeft, Clock, Goods, Calendar, Picture, List, EditPen, Check, Close } from '@element-plus/icons-vue'
import ManagementNavigation from '@/moon/management_navigation.vue'
import CommodityRejectAudit from './content/commodity_rejectAudit.vue'
import CommodityPassAudit from './content/commodity_passAudit.vue'

defineOptions(
    {name:'ManagementCommodityApply',
        components:{
            ManagementNavigation,
            CommodityRejectAudit,
            CommodityPassAudit
        }
    }
)

const Axios = axios.create({
    baseURL:'http://127.0.0.1:8000/api'
})


const mod = ref('CommodityRejectAudit')
const route = useRoute()
const router = useRouter()
const mall_id = ref(route.params.mall_id as string)
const shopping_id = ref(route.params.shopping_id as string)
const loading = ref(false)
const token = ref(localStorage.getItem('admin_access_token') || '')
const dialogVisible = ref(false)
const submitting = ref(false)
const currentComponent = ref()

function goBack() {
    router.back()
}
const title = ref('')

interface CommodityInfo {
    name: string
    time: string
    info: string
    img_list: string[]
    specification_list: Array<{
        specification?: string
        price?: number
        stock?: number
        [key: string]: any
    }>
    classify?: string
    types?: string
    classify_categorize?: number
}

const commodityInfo = ref<CommodityInfo | null>(null)

// 计算预览图片列表
const previewImageList = computed(() => {
    if (!commodityInfo.value?.img_list) return []
    return commodityInfo.value.img_list.map(img => `data:image/jpeg;base64,${img}`)
})

// 格式化规格数据为表格格式
const specificationTableData = computed(() => {
    if (!commodityInfo.value?.specification_list) return []
    console.log();
    
    return commodityInfo.value.specification_list.map((spec, index) => ({
        specification: spec.specs[0] || `规格${index + 1}`,
        price: spec.price || 0,
        stock: spec.stock || 0
    }))
})

async function getCommodityInfo() {
    try {
        loading.value = true
        const res = await Axios.get('/manage_get_commoidt_apply_detail',{
            params:{
                mall_id:Number(mall_id.value),
                shopping_id:Number(shopping_id.value)
            },
            headers:{
                'access-token': token.value
            }
        })
        
        if (res.data.current && res.data.data) {
            commodityInfo.value = {
                name: res.data.data.name || '',
                time: res.data.data.time || new Date().toLocaleString('zh-CN'),
                info: res.data.data.info || '',
                img_list: res.data.data.img_list || [],
                specification_list: res.data.data.specification_list || [],
                classify: res.data.data.classify || '',
                types: res.data.data.types || ''
            }
        } else {
            ElMessage.error(res.data.msg || '获取商品信息失败')
            commodityInfo.value = null
        }
    } catch (error: any) {
        console.error('获取商品信息失败:', error)
        ElMessage.error(error.response?.data?.msg || '获取商品信息失败，请稍后重试')
        commodityInfo.value = null
    } finally {
        loading.value = false
    }
}

// 拒绝审核
function rejectAudit() {
    dialogVisible.value = true
    title.value = '拒绝审核'
    mod.value = 'CommodityRejectAudit'
}


// 通过审核
function passAudit() {
    dialogVisible.value = true
    title.value = '通过审核'
    mod.value = 'CommodityPassAudit'
}

async function handleReject(reason?: string) {
    const trimedReason = String(reason || '').trim();
    console.log('拒绝理由:', reason);
    console.log('处理后的拒绝理由:', trimedReason);

    if (!reason || reason.trim() === '') {
        ElMessage.warning('请填写拒绝理由')
        return
    }

    submitting.value = true

    // TODO: 实现拒绝审核的API调用逻辑
    console.log('开始处理拒绝审核...')

    // 模拟API调用
    const formdata = new FormData()
    formdata.append('token', token.value)
    formdata.append('mall_id', mall_id.value)
    formdata.append('shopping_id', shopping_id.value)
    formdata.append('reason', trimedReason)
    const res = await Axios.post('/manage_commodity_rejectAudit', formdata)
    if (res.status == 200) {
        if (res.data.current) {
            ElMessage.success('审核拒绝成功')
            submitting.value = false
            dialogVisible.value = false
            router.push('/management_commodity')
        } else {
            ElMessage.error(res.data.msg || '审核拒绝失败')
        }
    }
}

function handleCancel() {
    dialogVisible.value = false
}

function triggerReject() {
    console.log('triggerReject 被调用')
    if (currentComponent.value && typeof currentComponent.value.sendReject === 'function') {
        console.log('调用子组件 sendReject 方法')
        currentComponent.value.sendReject()
    } else {
        console.log('currentComponent 或 sendReject 方法不存在', currentComponent.value)
    }
}

function triggerPass() {
    if (currentComponent.value && typeof currentComponent.value.handlePass === 'function') {
        currentComponent.value.handlePass()
    }
}

function handlePass(remark?: string) {
    submitting.value = true

    // TODO: 实现通过审核的API调用逻辑
    console.log('审核通过备注:', remark)

    // 模拟API调用
    setTimeout(() => {
        ElMessage.success('审核通过成功')
        submitting.value = false
        dialogVisible.value = false
        // 可以在这里添加页面刷新或其他后续操作
    }, 1500)
}

onMounted(async () => {
    console.log(mall_id.value,shopping_id.value);
    
    await getCommodityInfo()
})
</script>
<style scoped>
.commodity-detail-main {
    padding: 20px;
    background-color: #f5f7fa;
    min-height: calc(100vh - 120px);
    transition: background-color 0.3s ease;
}

.loading-container {
    padding: 20px;
}

.detail-container {
    max-width: 1200px;
    margin: 0 auto;
}

.detail-card {
    border-radius: 12px;
    overflow: hidden;
    transition: all 0.3s ease;
    margin-bottom: 20px;
    border: 1px solid #e4e7ed;
}

.detail-card:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 10px;
}

.header-icon {
    font-size: 20px;
    color: white;
}

.card-header h2,
.card-header h3 {
    margin: 0;
    color: white;
    font-size: 18px;
    font-weight: 600;
    transition: color 0.3s ease;
}

.commodity-descriptions {
    margin-top: 20px;
}

.commodity-name {
    font-size: 18px;
    font-weight: 600;
    color: #303133;
    transition: color 0.3s ease;
}

.commodity-info {
    color: #606266;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
    transition: color 0.3s ease;
}

.image-gallery {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 8px;
}

.gallery-image {
    width: 150px;
    height: 150px;
    border-radius: 8px;
    cursor: pointer;
    transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
    border: 1px solid #e4e7ed;
}

.gallery-image:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.specification-list {
    margin-top: 8px;
}

.price-text {
    color: #f56c6c;
    font-weight: 600;
    font-size: 16px;
}

/* 审核操作卡片样式 */
.action-card {
    margin-top: 20px;
}

.action-buttons {
    display: flex;
    justify-content: center;
    gap: 20px;
    padding: 20px 0;
}

.audit-button {
    min-width: 160px;
    height: 50px;
    font-size: 16px;
    font-weight: 600;
    border-radius: 8px;
    transition: all 0.3s ease;
}

.approve-button {
    background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
    border: none;
}

.approve-button:hover {
    background: linear-gradient(135deg, #5daf34 0%, #73c04d 100%);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(103, 194, 58, 0.4);
}

.reject-button {
    background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
    border: none;
}

.reject-button:hover {
    background: linear-gradient(135deg, #e64e4e 0%, #f56c6c 100%);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(245, 108, 108, 0.4);
}

.footer-content {
    text-align: center;
    color: darkgray;
}

:deep(.el-descriptions__label) {
    font-weight: 600;
    color: #606266;
    transition: color 0.3s ease;
}

:deep(.el-descriptions__content) {
    color: #303133;
    transition: color 0.3s ease;
}

:deep(.el-card__header) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
}

:deep(.el-card__header h2) {
    color: white;
}

/* 暗色主题样式 */
.dark .commodity-detail-main {
    background-color: #1a1a1a;
}

.dark .card-header h2 {
    color: #e5eaf3;
}

.dark .commodity-name {
    color: #e5eaf3;
}

.dark .commodity-info {
    color: #a8abb2;
}

.dark .time-wrapper {
    color: #a8abb2;
}

.dark .gallery-image {
    border-color: #4c4d4f;
}

.dark .gallery-image:hover {
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
    border-color: rgba(64, 158, 255, 0.5);
}

.dark .image-index {
    background: rgba(255, 255, 255, 0.2);
    color: #e5eaf3;
}

.dark :deep(.el-descriptions__label) {
    color: #a8abb2;
}

.dark :deep(.el-descriptions__content) {
    color: #e5eaf3;
}

.dark :deep(.el-descriptions__border) {
    border-color: #4c4d4f;
}

.dark :deep(.el-card) {
    background-color: #252525;
    border-color: #4c4d4f;
}

.dark :deep(.el-card__body) {
    background-color: #252525;
    color: #e5eaf3;
}

.dark :deep(.el-table) {
    background-color: #252525;
    color: #e5eaf3;
}

.dark :deep(.el-table th) {
    background-color: #2d2d2d;
    color: #e5eaf3;
    border-color: #4c4d4f;
}

.dark :deep(.el-table td) {
    background-color: #252525;
    color: #e5eaf3;
    border-color: #4c4d4f;
}

.dark :deep(.el-table tr:hover > td) {
    background-color: #2d2d2d;
}

.dark :deep(.el-table--border) {
    border-color: #4c4d4f;
}

.dark :deep(.el-empty__description) {
    color: #a8abb2;
}

.dark .footer-content {
    color: #a8abb2;
}

/* 对话框样式 */
.dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 16px 24px 24px;
    background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
    border-top: 1px solid #e4e7ed;
    border-radius: 0 0 12px 12px;
}

.cancel-btn {
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.3s ease;
    border: 1px solid #dcdfe6;
}

.cancel-btn:hover {
    border-color: #f56c6c;
    color: #f56c6c;
    background-color: rgba(245, 108, 108, 0.04);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(245, 108, 108, 0.15);
}

.confirm-btn {
    border-radius: 8px;
    font-weight: 500;
    background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
    border: none;
    transition: all 0.3s ease;
}

.confirm-btn:hover:not(.is-loading) {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(245, 108, 108, 0.3);
    background: linear-gradient(135deg, #f78989 0%, #fab1a0 100%);
}

.confirm-btn.is-loading {
    background: #f56c6c;
}

.pass-btn {
    border-radius: 8px;
    font-weight: 500;
    background: linear-gradient(135deg, #67c23a 0%, #95d475 100%);
    border: none;
    transition: all 0.3s ease;
}

.pass-btn:hover:not(.is-loading) {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(103, 194, 58, 0.3);
    background: linear-gradient(135deg, #95d475 0%, #b3e0a8 100%);
}

.pass-btn.is-loading {
    background: #67c23a;
}

.reject-btn {
    border-radius: 8px;
    font-weight: 500;
    background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
    border: none;
    transition: all 0.3s ease;
}

.reject-btn:hover:not(.is-loading) {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(245, 108, 108, 0.3);
    background: linear-gradient(135deg, #f78989 0%, #fab1a0 100%);
}

.reject-btn.is-loading {
    background: #f56c6c;
}

/* 对话框内容样式 */
:deep(.el-dialog) {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
}

:deep(.el-dialog__header) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    margin: 0;
    padding: 20px 24px;
    border-bottom: none;
}

:deep(.el-dialog__title) {
    color: white;
    font-size: 18px;
    font-weight: 600;
}

:deep(.el-dialog__headerbtn) {
    top: 16px;
    right: 20px;
}

:deep(.el-dialog__headerbtn .el-dialog__close) {
    color: white;
    font-size: 20px;
}

:deep(.el-dialog__body) {
    padding: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .image-gallery {
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 12px;
    }
    
    .gallery-image {
        height: 120px;
    }
    
    .action-buttons {
        flex-direction: column;
        gap: 12px;
    }
    
    .audit-button {
        width: 100%;
    }
    
    .action-bar {
        flex-direction: column;
        gap: 12px;
        align-items: flex-start;
    }
}

/* 对话框暗色主题样式 */
.dark .dialog-footer {
    background: var(--color-background);
    border-top-color: var(--color-border);
}

.dark .cancel-btn {
    border-color: var(--color-border);
    color: var(--color-text);
}

.dark .cancel-btn:hover {
    border-color: #f87171;
    color: #f87171;
    background-color: rgba(248, 113, 113, 0.1);
}

.dark :deep(.el-dialog) {
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
}

.dark :deep(.el-dialog__header) {
    background: linear-gradient(135deg, #4c1d95 0%, #7c3aed 100%);
}

.dark :deep(.el-dialog__body) {
    background: var(--color-background);
}

.dark .pass-btn {
    background: linear-gradient(135deg, #4ade80 0%, #6ee7b7 100%);
}

.dark .pass-btn:hover:not(.is-loading) {
    background: linear-gradient(135deg, #6ee7b7 0%, #86efac 100%);
}

.dark .pass-btn.is-loading {
    background: #4ade80;
}

.dark .reject-btn {
    background: linear-gradient(135deg, #f87171 0%, #fca5a5 100%);
}

.dark .reject-btn:hover:not(.is-loading) {
    background: linear-gradient(135deg, #fca5a5 0%, #fecaca 100%);
}

.dark .reject-btn.is-loading {
    background: #f87171;
}
</style>