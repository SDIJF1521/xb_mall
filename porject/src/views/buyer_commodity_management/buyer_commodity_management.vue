<template>
   <el-container>
        <el-container>
           <BuyerNavigation/>
                <el-container>
                  <el-header>
                        <BuyerHead/>
                    </el-header>
                    <el-main>
                        <div class="commodity-management-container">
                            <h2 class="page-title">商品管理中心</h2>
                            <p class="page-subtitle">高效管理您的商品，提升销售效率</p>

                            <div class="card-grid">
                                <el-card class="action-card add-commodity" shadow="hover" >
                                    <template #header>
                                        <div class="card-header">
                                            <el-icon class="card-icon" size="24"><Plus /></el-icon>
                                            <span class="card-title">新增商品</span>
                                        </div>
                                    </template>
                                    <div class="card-content">
                                        <el-icon class="feature-icon" size="64"><Goods /></el-icon>
                                        <p class="card-description">添加新商品，丰富您的商品库存</p>
                                        <el-button type="primary" @click="toAddCommodity" plain>立即添加</el-button>
                                    </div>
                                </el-card>

                                <el-card class="action-card manage-commodity" shadow="hover">
                                    <template #header>
                                        <div class="card-header">
                                            <el-icon class="card-icon" size="24"><Setting /></el-icon>
                                            <span class="card-title">商品管理</span>
                                        </div>
                                    </template>
                                    <div class="card-content">
                                        <el-icon class="feature-icon" size="64"><Management /></el-icon>
                                        <p class="card-description">全面管理商品信息和库存</p>
                                        <el-button type="success" @click="toCommodityManage" plain>进入管理</el-button>
                                    </div>
                                </el-card>

                                <el-card class="action-card category-manage" shadow="hover">
                                    <template #header>
                                        <div class="card-header">
                                            <el-icon class="card-icon" size="24"><Grid /></el-icon>
                                            <span class="card-title">分类管理</span>
                                        </div>
                                    </template>
                                    <div class="card-content">
                                        <el-icon class="feature-icon" size="64"><Collection /></el-icon>
                                        <p class="card-description">管理商品分类，优化商品展示</p>
                                        <el-button type="warning" @click="toCategoryManage" plain>分类设置</el-button>
                                    </div>
                                </el-card>

                                <el-card class="action-card inventory-manage" shadow="hover">
                                    <template #header>
                                        <div class="card-header">
                                            <el-icon class="card-icon" size="24"><Histogram /></el-icon>
                                            <span class="card-title">库存管理</span>
                                        </div>
                                    </template>
                                    <div class="card-content">
                                        <el-icon class="feature-icon" size="64"><TrendCharts /></el-icon>
                                        <p class="card-description">实时监控库存状态，智能补货</p>
                                        <el-button type="info" @click="toInventoryManage" plain>库存监控</el-button>
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
import {ref,onMounted} from 'vue'
import router from "@/router"
import BuyerTheme from '@/moon/buyer_theme'
import BuyerHead from '@/moon/buyer_head.vue'
import BuyerNavigation from '@/moon/buyer_navigation.vue'
import { useBuyerManagementSelectStore } from '@/moon/buyer_management_select';
import { Plus, Setting, Grid, Histogram, Goods, Management, Collection, TrendCharts } from '@element-plus/icons-vue'

defineOptions({
    name:'BuyerCommodityManagement',
    components:{
        BuyerTheme,
        BuyerHead,
        BuyerNavigation,
        Plus,
        Setting,
        Grid,
        Histogram,
        Goods,
        Management,
        Collection,
        TrendCharts
    }
})
onMounted(()=>{
  new BuyerTheme().toggleTheme(true)
   // 初始化store
  useBuyerManagementSelectStore().init()
})

// 跳转到添加商品页面
function toAddCommodity(){
    const store = useBuyerManagementSelectStore()
    store.setToUel('/buyer_commodity_add')
    router.push({name:'BuyerSelect'})
}
// 跳转到商品管理页面
function toCommodityManage(){
    const store = useBuyerManagementSelectStore()
    store.setToUel('/buyer_commodity_list')
    router.push({name:'BuyerSelect'})
}
// 跳转到分类管理页面
function toCategoryManage(){
    const store = useBuyerManagementSelectStore()
    store.setToUel('/buyer_category_manage')
    router.push({name:'BuyerSelect'})
}
// 跳转到库存管理页面
function toInventoryManage(){
    const store = useBuyerManagementSelectStore()
    store.setToUel('/buyer_inventory_manage')
    router.push({name:'BuyerSelect'})
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

    .commodity-management-container {
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

    .action-card.add-commodity {
        border-left: 4px solid #409eff;
    }

    .action-card.manage-commodity {
        border-left: 4px solid #67c23a;
    }

    .action-card.category-manage {
        border-left: 4px solid #e6a23c;
    }

    .action-card.inventory-manage {
        border-left: 4px solid #909399;
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

    .manage-commodity .card-icon {
        color: #67c23a;
    }

    .category-manage .card-icon {
        color: #e6a23c;
    }

    .inventory-manage .card-icon {
        color: #909399;
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

    .add-commodity .feature-icon {
        color: #409eff;
    }

    .manage-commodity .feature-icon {
        color: #67c23a;
    }

    .category-manage .feature-icon {
        color: #e6a23c;
    }

    .inventory-manage .feature-icon {
        color: #909399;
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
        .commodity-management-container {
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
