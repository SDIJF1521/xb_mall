<template>
    
    <el-menu
        default-active="1-1"
        class="el-menu-vertical-demo"
        @select="handleSelect"
    >

    <el-sub-menu index="1">
        <template class="text" #title>
             <el-icon><icon-building-store/></el-icon> 
            <span>商家管理</span>
        </template>
        <el-menu-item index="1-1">商家申请合验</el-menu-item>
        <el-menu-item index="1-2">商家账号管理</el-menu-item>
    </el-sub-menu>

    

    <el-menu-item index="2">
        <el-icon> <icon-users/></el-icon> 
        <span>商城用户管理</span>
    </el-menu-item>

    <el-menu-item index="3">
        <el-icon> <icon-user/></el-icon> 
        <span>后台用户管理</span>
    </el-menu-item>
    </el-menu>
</template>
<script setup lang="ts">
import { IconBuildingStore, IconUsers, IconUser } from '@tabler/icons-vue';
defineOptions({
    name:'UserManagmentNavigation',
    components:{
        IconBuildingStore,
        IconUsers,
        IconUser
    }
})
const emit = defineEmits(['menu-selected']);
//导航栏响应函数
const handleSelect = (index: string) => {
  console.log('选中的菜单 index:', index);
  emit('menu-selected', index);
}
</script>