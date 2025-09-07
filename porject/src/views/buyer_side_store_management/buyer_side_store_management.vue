<template>
    <el-container>
        <el-container>
            <BuyerNavigation/>
                <el-container>
                    <el-header>
                        <BuyerHead/>
                    </el-header>
                    <el-main>
                        <div class="store-management-container">
                            <h2 class="page-title">店铺管理中心</h2>
                            <p class="page-subtitle">高效管理您的店铺，提升运营效率</p>
                            
                            <div class="card-grid">
                                <el-card class="action-card add-store" shadow="hover" >
                                    <template #header>
                                        <div class="card-header">
                                            <el-icon class="card-icon" size="24"><Plus /></el-icon>
                                            <span class="card-title">新增店铺</span>
                                        </div>
                                    </template>
                                    <div class="card-content">
                                        <el-icon class="feature-icon" size="64"><Plus /></el-icon>
                                        <p class="card-description">创建新的店铺，开始您的电商之旅</p>
                                        <el-button type="primary" @click="toAddMall" plain>立即创建</el-button>
                                    </div>
                                </el-card>

                                <el-card class="action-card manage-store" shadow="hover">
                                    <template #header>
                                        <div class="card-header">
                                            <el-icon class="card-icon" size="24"><Setting /></el-icon>
                                            <span class="card-title">店铺管理</span>
                                        </div>
                                    </template>
                                    <div class="card-content">
                                        <el-icon class="feature-icon" size="64"><Shop /></el-icon>
                                        <p class="card-description">全面管理店铺信息、商品和订单</p>
                                        <el-button type="success" plain>进入管理</el-button>
                                    </div>
                                </el-card>

                                <el-card class="action-card remove-store" shadow="hover">
                                    <template #header>
                                        <div class="card-header">
                                            <el-icon class="card-icon" size="24"><Delete /></el-icon>
                                            <span class="card-title">店铺移除</span>
                                        </div>
                                    </template>
                                    <div class="card-content">
                                        <el-icon class="feature-icon" size="64"><Warning /></el-icon>
                                        <p class="card-description">安全移除不需要的店铺</p>
                                        <el-button type="danger" plain>谨慎操作</el-button>
                                    </div>
                                </el-card>
                            </div>
                        </div>
                    </el-main>
                </el-container>
        </el-container>
       <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
    </el-container>
</template>
<script setup lang="ts">
import {ref, onMounted} from "vue"
import router from "@/router"
import BuyerNavigation from '@/moon/buyer_navigation.vue'
import BuyerHead from '@/moon/buyer_head.vue'
import {Delete} from '@element-plus/icons-vue'

defineOptions({
    name: "BuyerSideStoreManagement",
    components:{
        BuyerNavigation,
        BuyerHead,
        Delete
    }
})
onMounted(()=>{
    document.documentElement.classList.add('dark')
})

// 跳转到添加店铺页面
function toAddMall(){
    router.push('/buyer_add_mall')
}
</script>
<style scoped>
    .footer-content {
        text-align: center;
        color: darkgray;
    }
    .el-header {
        border-bottom: 1px solid #514d4d;
        padding-bottom: 10px;
        margin-bottom: 10px;
    }
    
    .store-management-container {
        padding: 20px;
        max-width: 1200px;
        margin: 0 auto;
    }

    .page-title {
        text-align: center;
        font-size: 32px;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 8px;
    }

    .page-subtitle {
        text-align: center;
        font-size: 16px;
        color: #7f8c8d;
        margin-bottom: 40px;
    }

    .card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
        gap: 30px;
        justify-items: center;
    }

    .action-card {
        width: 100%;
        max-width: 380px;
        border-radius: 12px;
        transition: all 0.3s ease;
        cursor: pointer;
    }

    .action-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
    }

    .action-card.add-store {
        border-left: 4px solid #409eff;
    }

    .action-card.manage-store {
        border-left: 4px solid #67c23a;
    }

    .action-card.remove-store {
        border-left: 4px solid #f56c6c;
    }

    .card-header {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 16px 0;
    }

    .card-icon {
        color: #409eff;
    }

    .manage-store .card-icon {
        color: #67c23a;
    }

    .remove-store .card-icon {
        color: #f56c6c;
    }

    .card-title {
        font-size: 18px;
        font-weight: 600;
        color: #2c3e50;
    }

    .card-content {
        text-align: center;
        padding: 20px 0;
    }

    .feature-icon {
        margin-bottom: 16px;
        color: #909399;
    }

    .add-store .feature-icon {
        color: #409eff;
    }

    .manage-store .feature-icon {
        color: #67c23a;
    }

    .remove-store .feature-icon {
        color: #f56c6c;
    }

    .card-description {
        font-size: 14px;
        color: #606266;
        margin-bottom: 20px;
        line-height: 1.6;
    }

    .el-button {
        width: 100%;
        max-width: 200px;
    }

    /* 响应式设计 */
    @media (max-width: 768px) {
        .store-management-container {
            padding: 15px;
        }

        .page-title {
            font-size: 28px;
        }

        .page-subtitle {
            font-size: 14px;
            margin-bottom: 30px;
        }

        .card-grid {
            grid-template-columns: 1fr;
            gap: 20px;
        }

        .action-card {
            max-width: 100%;
        }
    }

    @media (max-width: 480px) {
        .card-content {
            padding: 15px 0;
        }

        .feature-icon {
            font-size: 48px !important;
        }
    }
</style>