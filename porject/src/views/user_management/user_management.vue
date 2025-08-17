<template>
  <el-container>
    <el-header>
      <ManagementNavigation/>
    </el-header>
    <el-container>
      <el-aside width="250px">

        <UserManagmentNavigation @menu-selected="handleMenuSelect" />
      </el-aside>
      <el-main>
        <component :is = "mods"/>
      </el-main>
    </el-container>
      <el-footer class="footer-content">版权所有 © [小白的商城]，保留所有权利。</el-footer>
  </el-container>
</template>
<script lang="ts" setup>
import {ref} from 'vue'
import ManagementNavigation from '@/moon/management_navigation.vue'
import UserManagmentNavigation from './content/user_managment_navigation.vue'
import MallApplyManagement from './content/mall_apply_management.vue'
import BusinessManagement from './content/business_management.vue'

const mods = ref('MallApplyManagement')
defineOptions({name:'UserManagement',
                components:{
                  ManagementNavigation,
                  UserManagmentNavigation,
                  MallApplyManagement,
                  BusinessManagement
                }
                })
const handleMenuSelect = (data:string) =>{
  console.log(data);
  if (data == '1-1'){
    mods.value = 'MallApplyManagement'
  }else if (data == '1-2'){
    mods.value = 'BusinessManagement'
  }
}
</script>
<style scoped>

.el-header {
  padding: 0 20px;
  height: auto;
  min-height: 60px;
}

.el-main {
  padding: 20px;
  flex: 1;
}
.footer-content {
  text-align: center;
  color: darkgray;
}

:deep() .el-main {
  border: 2px solid transparent;
  border-image: linear-gradient(to right, #383e4b, #3d3545) 1;
}
</style>