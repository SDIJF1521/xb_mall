<template>
 <el-container>
        <el-container>
            <BuyerNavigation />
            <el-container>
                <el-header>
                    <BuyerHead/>
                </el-header>
                <el-main>
                  <div class = "set-list-container">
                    <SetList/>
                  </div>
                </el-main>
            </el-container>
        </el-container>
        <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
    </el-container>
</template>
<script setup lang="ts">
import {ref,onMounted} from 'vue'
import axios from 'axios'
import BuyerHead from '@/moon/buyer_head.vue'
import BuyerNavigation from '@/moon/buyer_navigation.vue'
import BuyerTheme from '@/moon/buyer_theme'
import SetList from '@/views/buyer_set/content/SetList.vue'

defineOptions({name:'BuyerSet',
                components:{
                    BuyerHead,
                    BuyerNavigation
                }
              })

onMounted(()=>{
    new BuyerTheme().initTheme()
})


</script>
<style lang="scss">
  .footer-content {
          text-align: center;
          color: darkgray;
          }
  .el-header {
          border-bottom: 1px solid #514d4d;
          padding-bottom: 10px;
          margin-bottom: 10px;
      }
  // 内容组件居中显示
  .set-list-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
  }

</style>
