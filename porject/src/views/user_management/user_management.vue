<template>
    <el-container>
      <el-header>
        <ManagementNavigation/>
      </el-header>
      <el-main>Main</el-main>
      <el-footer class="footer-content">版权所有 © [小白的商城]，保留所有权利。</el-footer>
    </el-container>
</template>
<script lang="ts" setup>
import ManagementNavigation from '@/moon/management_navigation.vue'

defineOptions({name:'UserManagement',
                components:{ManagementNavigation}
                })
</script>
<style scoped>
.footer-content {
  text-align: center;
  color: darkgray;
}

</style>