<template>
        <el-menu
            :default-active="selected"
            :collapse="store.isMouseInside"
            @mouseenter="store.handleMouseLeave()"
            @mouseleave="store.handleMouseEnter()"
            @select="handleSelect"

        >
            <el-menu-item index="0" disabled>
                <el-icon><Eleme/></el-icon>

                <span slot="title">
                    欢迎来到买家端后台
                </span>

            </el-menu-item>

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
                <el-icon><Service/></el-icon>
                <span slot="title">客服管理</span>

            </el-menu-item>
            <el-menu-item index="7">
                <el-icon><DocumentCopy/></el-icon>
                <span slot="title">评论管理</span>
            </el-menu-item>
            <el-menu-item index="8">
                <el-icon><Box/></el-icon>
                <span slot="title">物流管理</span>
            </el-menu-item>
            <el-menu-item index = "9">
                <el-icon><Setting/></el-icon>
                <span slot="title">系统管理</span>

            </el-menu-item>

        </el-menu>


</template>
<script setup lang="ts">
import { ref,onMounted} from 'vue'
import router from '@/router'
import { useRoute } from 'vue-router';
import {Eleme,Odometer,Shop,List,Handbag,User,DocumentCopy,Box,Setting,Service} from '@element-plus/icons-vue'
import { useBuyerNavigationStore } from '@/moon/buyer_navigatiom_pinia'
// 引入导航栏状态管理
const store = useBuyerNavigationStore();

const selected = ref('1')

// 监听页面路由变化，更新导航栏选中项
onMounted(()=>{
    const route = useRoute();
    switch(route.path){
        case '/buyer_index':
            selected.value = '1'
            break;
        case '/buyer_store_management':
            selected.value = '2'
            break;


    }
})

// 处理菜单选择事件
const handleSelect = (index:string)=>{
    console.log('选中的菜单 index:',index);
    if (index =='1'){
        router.push('/buyer_index')
    }else if (index =='2'){
        router.push('/buyer_store_management')
    }
}


defineOptions({
    name:'BuyerNavigation'})
</script>
