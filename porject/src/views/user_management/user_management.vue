<template>
  <el-container style="gap: 15px;">
      <el-header>
        <ManagementNavigation/>
      </el-header>
    <el-container>
      <el-aside width="250px">

        <UserManagmentNavigation/>

      </el-aside>
      <el-main>
        内容
      </el-main>
    </el-container>
      <el-footer class="footer-content">版权所有 © [小白的商城]，保留所有权利。</el-footer>
  </el-container>
</template>
<script lang="ts" setup>
import ManagementNavigation from '@/moon/management_navigation.vue'
import UserManagmentNavigation from './content/user_managment_navigation.vue'

defineOptions({name:'UserManagement',
                components:{
                  ManagementNavigation,
                  UserManagmentNavigation,
                }
                })
</script>
<style scoped>
.footer-content {
  text-align: center;
  color: darkgray;
}
</style>