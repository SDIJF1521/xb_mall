<template>
    <el-container>
      <el-header>
        <ManagementNavigation/>
      </el-header>
      <el-main>
        <ExampleView/>
      </el-main>
      <el-footer class="footer-content">版权所有 © [小白的商城]，保留所有权利。</el-footer>
    </el-container>
</template>
<script lang="ts" setup>
import {ref, onMounted} from 'vue';
import ManagementNavigation from '@/moon/management_navigation.vue'
import ExampleView from './content/online_people_counting.vue'
const user_name = ref()
defineOptions({
  name:'Management',
  components:{
    ManagementNavigation,
    ExampleView
  }
})
</script>
<style scoped>
/* 响应式布局样式 */
el-container {
  min-height: 100vh;
  width: 100%;
}

el-header {
  padding: 0 20px;
  height: auto;
  min-height: 60px;
}

el-main {
  padding: 20px;
  flex: 1;
}

.footer-content {
  text-align: center;
  color: darkgray;
  padding: 15px 0;
}

/* 媒体查询 - 适配移动设备 */
@media screen and (max-width: 768px) {
  el-header {
    padding: 0 10px;
  }
  
  el-main {
    padding: 10px;
  }
  
  .footer-content {
    font-size: 12px;
    padding: 10px 0;
  }
}
</style>