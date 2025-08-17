<template>
    <div>
        <h4>欢迎来到卖家端后台</h4>
        <el-menu
            default-active="1"
        >
            <el-menu-item index="1">
                <el-icon><Odometer/></el-icon>
                <span slot="title">仪表盘</span>
            </el-menu-item>
            <el-menu-item index="2">
                <el-icon><Shop/></el-icon>
                <span slot='title'>店铺管理</span>
            </el-menu-item>
            <el-menu-item index="3">
                <el-icon><List/></el-icon>
                <span slot="title">订单管理</span>
            </el-menu-item>
            <el-menu-item index="4">
                <el-icon><Handbag/></el-icon>
                <span slot="title">商品管理</span>
            </el-menu-item>
            <el-menu-item index="5">
                <el-icon><User/></el-icon>
                <span slot="title">用户管理</span>
            </el-menu-item>
            <el-menu-item index="6">
                <el-icon><DocumentCopy/></el-icon>
                <span slot="title">评论管理</span>
            </el-menu-item>
            <el-menu-item index="7">
                <el-icon><Box/></el-icon>
                <span slot="title">物流管理</span>
            </el-menu-item>
            <el-menu-item index = "8">
                <el-icon><Setting/></el-icon>
                <span slot="title">系统管理</span>

            </el-menu-item>
            
        </el-menu>
    </div>
        
    
</template>
<script setup lang="ts">
import {Odometer,Shop,List,Handbag,User,DocumentCopy,Box,Setting} from '@element-plus/icons-vue'







defineOptions({
    name:'BuyerNavigation'})
</script>