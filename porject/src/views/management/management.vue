<template>
    <el-container>
      <el-header>
        <ManagementNavigation/>
      </el-header>
      <el-main>
        <div class="data_panel">
          <ExampleView/>
          <NewlyIncreasedNumberPeople/>
          <NumberMerchants/>
        </div>
        <div>
          <MerchantClientRatio/>
        </div>


      </el-main>
      <el-footer class="footer-content">版权所有 © [小白的商城]，保留所有权利。</el-footer>
    </el-container>
</template>
<script lang="ts" setup>
import {ref} from 'vue';
import ManagementNavigation from '@/moon/management_navigation.vue'
import ExampleView from './content/online_people_counting.vue'
import NewlyIncreasedNumberPeople from './content/newly_increased_number_people.vue'
import NumberMerchants from './content/number_merchants.vue'
import MerchantClientRatio from './content/merchant_client_ratio.vue'

const user_name = ref()
defineOptions({
  name:'Management',
  components:{
    ManagementNavigation,
    ExampleView,
    NewlyIncreasedNumberPeople,
    NumberMerchants,
    MerchantClientRatio
  }
})
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
.data_panel{
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 15px;
}
</style>
