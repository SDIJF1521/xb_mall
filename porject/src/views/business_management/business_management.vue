<template>
    <el-container>
      <el-header>
        <ManagementNavigation />
      </el-header>
      <!-- 内容 -->
      <el-main>
        <div class="main">
          <!-- 信息显示区 -->
           <el-descriptions title="商家信息" border>
            <el-descriptions-item
              :rowspan="2"
              :width="140"
              label="头像"
              align="center"
            >
              <el-image
                style="width: 100px; height: 100px"
                :src="from_data[6]"

              />
            </el-descriptions-item>
            <el-descriptions-item label="用户名">{{from_data[0]}}</el-descriptions-item>

            <el-descriptions-item label="手机号">{{ from_data[1] }}</el-descriptions-item>

            <el-descriptions-item label="商家名称">{{from_data[2]}}</el-descriptions-item>

            <el-descriptions-item label="状态">
              <el-tag v-if="from_data[3] == '1'" size="small">正常</el-tag>


              <el-tag v-else type="danger" size="small">异常</el-tag>

            </el-descriptions-item>
            <el-descriptions-item label="店铺数量">{{from_data[4]}}</el-descriptions-item>

            <el-descriptions-item label="店铺描述">{{from_data[5]}}</el-descriptions-item>

          </el-descriptions>
        </div>
      </el-main>

      <el-footer class="footer-content">版权所有 © [小白的商城]，保留所有权利。</el-footer>
    </el-container>
</template>
<script setup lang="ts">
import { ref,onMounted } from 'vue';
import { useRoute } from 'vue-router';

import { ElMessage } from 'element-plus';
import axios from 'axios';
import ManagementNavigation from '@/moon/management_navigation.vue'

defineOptions({
    name:'BusinessManagement',
    components:{
        ManagementNavigation
    }
    })

// 路由参数
const route = useRoute();

const from_data = ref(['username','123456','小白','1','0','***','https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'])

const Axios = axios.create({
    baseURL:'http://127.0.0.1:8000/api',
})

onMounted(async ()=>{
  const from_url_data = new FormData();
  from_url_data.append('token',localStorage.getItem('admin_access_token')||'');
  from_url_data.append('name',String(route.params.id)||'')

  

  await Axios.post('/management_mall_info',from_url_data)

  .then(res=>{
    if (res.status == 200){
      if (res.data.current){
        from_data.value[0] = res.data.mall_info[0]
        from_data.value[1] = res.data.mall_info[2]
        from_data.value[2] = res.data.mall_info[1]
        from_data.value[3] = res.data.mall_info[5]
        from_data.value[4] = res.data.mall_info[4]
        from_data.value[5] = res.data.mall_info[3]
        from_data.value[6] = 'data:image/png;base64,' + res.data.mall_info[6]







        console.log(res.data.mall_info);
      }
    }
    
  })

  console.log(route.params.id);
  
})



</script>
<style scoped>
.footer-content {
  text-align: center;
  color: darkgray;
}
.main{
  margin-bottom: 10px;
}
</style>