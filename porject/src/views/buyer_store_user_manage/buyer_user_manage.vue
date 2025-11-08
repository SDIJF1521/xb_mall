<template>
    <el-container>
        <el-container>
            <BuyerNavigation/>
                <el-container>
                    <el-header>
                        <BuyerHead/>
                    </el-header>
                    <el-main>
                        <div class="user-management-container">
                            <h2 class="page-title">用户管理中心</h2>
                            <p class="page-subtitle">高效管理用户，提升运营效率</p>

                            <div class="card-grid">
                                <el-card class="action-card user-list" shadow="hover">
                                    <template #header>
                                        <div class="card-header">
                                            <el-icon class="card-icon" size="24"><User /></el-icon>
                                            <span class="card-title">用户列表</span>
                                        </div>
                                    </template>
                                    <div class="card-content">
                                        <el-icon class="feature-icon" size="64"><UserFilled /></el-icon>
                                        <p class="card-description">查看和管理所有用户信息</p>
                                        <el-button type="primary" @click="toUserList" plain>进入管理</el-button>
                                    </div>
                                </el-card>

                                <el-card class="action-card role-management" shadow="hover">
                                    <template #header>
                                        <div class="card-header">
                                            <el-icon class="card-icon" size="24"><Avatar /></el-icon>
                                            <span class="card-title">角色权限</span>
                                        </div>
                                    </template>
                                    <div class="card-content">
                                        <el-icon class="feature-icon" size="64"><Key /></el-icon>
                                        <p class="card-description">管理用户角色和权限配置</p>
                                        <el-button type="success" @click="toRoleManage" plain>权限管理</el-button>
                                    </div>
                                </el-card>

                                <el-card class="action-card user-statistics" shadow="hover">
                                    <template #header>
                                        <div class="card-header">
                                            <el-icon class="card-icon" size="24"><TrendCharts /></el-icon>
                                            <span class="card-title">用户统计</span>
                                        </div>
                                    </template>
                                    <div class="card-content">
                                        <el-icon class="feature-icon" size="64"><DataAnalysis /></el-icon>
                                        <p class="card-description">查看用户数据统计分析</p>
                                        <el-button type="warning" @click="toUserStats" plain>查看统计</el-button>
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
import BuyerTheme from '@/moon/buyer_theme';
import { User, UserFilled, Avatar, Key, TrendCharts, DataAnalysis } from '@element-plus/icons-vue';

defineOptions({
    name: "BuyerUserManage",
    components:{
        BuyerNavigation
    }
})

onMounted(()=>{
   new BuyerTheme().toggleTheme(true)
})

// 跳转到用户列表页面
function toUserList(){
    // TODO: 实现跳转到用户列表页面
    router.push({name:'BuyerUserList'})
}

// 跳转到角色管理页面
function toRoleManage(){
    // TODO: 实现跳转到角色管理页面
    console.log('跳转到角色管理页面')
}

// 跳转到用户统计页面
function toUserStats(){
    // TODO: 实现跳转到用户统计页面
    console.log('跳转到用户统计页面')
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

    .user-management-container {
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

    .action-card.user-list {
        border-left: 4px solid #409eff;
    }

    .action-card.role-management {
        border-left: 4px solid #67c23a;
    }

    .action-card.user-statistics {
        border-left: 4px solid #e6a23c;
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

    .role-management .card-icon {
        color: #67c23a;
    }

    .user-statistics .card-icon {
        color: #e6a23c;
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

    .user-list .feature-icon {
        color: #409eff;
    }

    .role-management .feature-icon {
        color: #67c23a;
    }

    .user-statistics .feature-icon {
        color: #e6a23c;
    }

    .card-description {
        font-size: 14px;
        color: #606266;
        margin-bottom: 20px;
        line-height: 1.6;
        min-height: 40px;
    }

    .el-button {
        width: 100%;
        max-width: 200px;
    }

    /* 响应式设计 */
    @media (max-width: 768px) {
        .user-management-container {
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
