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

<style scoped>

.el-menu-vertical-demo {
  border-right: none;
  height: calc(100vh - 120px);
  padding: 20px 10px;
}

.el-menu-vertical-demo .el-menu-item {
  height: 48px;
  line-height: 48px;
  margin-bottom: 8px;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
  position: relative;
}

.el-menu-vertical-demo .el-menu-item:hover {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  transform: translateX(4px);
}

.el-menu-vertical-demo .el-menu-item.is-active {
  background-color: var(--el-color-primary);
  color: white;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.el-menu-vertical-demo .el-menu-item.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 24px;
  background-color: white;
  border-radius: 2px;
}

.el-menu-vertical-demo .el-icon {
  margin-right: 8px;
  font-size: 16px;
}

/* 暗色主题适配 */
.dark .el-menu-vertical-demo .el-menu-item:hover {
  background-color: rgba(64, 158, 255, 0.1);
  color: #409eff;
}

.dark .el-menu-vertical-demo .el-menu-item.is-active {
  background-color: #409eff;
  color: white;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.4);
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .el-menu-vertical-demo {
    padding: 10px 5px;
  }

  .el-menu-vertical-demo .el-menu-item {
    height: 44px;
    line-height: 44px;
    font-size: 13px;
  }
}

.el-main {
  padding: 20px;
  flex: 1;
}
</style>