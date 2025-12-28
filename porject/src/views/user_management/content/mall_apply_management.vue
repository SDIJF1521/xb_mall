<template>
    <div class="list-container">
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="mall_apply.length > 0">
          <ul>
            <li v-for="(item, index) in mall_apply" :key="index" @click="skip(item[0])">{{ item[0] }}</li>
          </ul>
          <div style="display: flex; justify-content: center; margin-top: 20px;">
            <el-pagination
              :page-size="20"
              :pager-count="11"
              layout="prev, pager, next"
              :total="page"
            />
          </div>
        </div>
        <el-empty v-else description="暂无数据" />
    </div>
</template>
<script setup lang="ts">
import {ref,onMounted,onUnmounted} from 'vue'
import axios from 'axios';
import { ElMessage } from 'element-plus';
import router from '@/router';

const page = ref(1)
defineOptions({name:'MallApplyManagement'})
// 定义接口类型
interface ApplyItem {
  [key: number]: any;
}

interface ApiResponse {
  current: boolean;
  apply_list: ApplyItem[];
  msg?: string;
  page: number;
}

const Axios = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
  });

const mall_apply = ref<ApplyItem[]>([]);
const loading = ref<boolean>(false);
let intervalId: number | undefined;

const checkToken = (): string => {
  const token = localStorage.getItem('admin_access_token');
  if (!token) {
    ElMessage.error('请先登录');
  }
  return token || '';
};

const skip = (id:string) =>{
  router.push({name:'AuditApplySeller',params:{id:id}})
}

onMounted(async() =>{
  const fetchData = async () => {
    try {
      const token = checkToken();
      if (!token) return;

      loading.value = true;
      const formdata = new FormData();
      formdata.append('token', token);
      const response = await Axios.post<ApiResponse>('/get_apply_seller_list', formdata);
      console.log(response.data);
      

      if (response.data.current && Array.isArray(response.data.apply_list)) {
        mall_apply.value = response.data.apply_list;
        page.value = response.data.page;
      } else {
        ElMessage.warning(response.data.msg || '获取数据失败');
        mall_apply.value = [];
      }
    } catch (error) {
      console.error('请求失败', error);
      ElMessage.error('网络错误，无法获取数据');
      mall_apply.value = [];
    } finally {
      loading.value = false;
    }
  };

  // 立即执行一次
  fetchData();
  // 设置定时器，每30秒执行一次
  intervalId = window.setInterval(fetchData, 30000);
})

onUnmounted(() => {
  if (intervalId) {
    window.clearInterval(intervalId);
  }
})
</script>
<style scoped>
.loading {
  text-align: center;
  padding: 20px;
  color: #666;
}
.no-data {
  text-align: center;
  padding: 20px;
  color: #999;
}
ul {
  list-style: none;
  padding: 0;
}
li {
  padding: 12px 16px;
  text-align: center;
  border-radius: 6px;
  margin-bottom: 8px;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  border-image: linear-gradient(to right, #ec8e8c 0%, #ad8be8 100%) 1;
  box-shadow: 0 0 5px rgba(230, 43, 43, 0.5);
}

li:hover {
  transform: translateY(-2px);
  border-image: linear-gradient(to right, #f1a09f 0%, #ad8be8 100%) 1;
  box-shadow: 0 0 15px rgba(254, 79, 112, 0.8);
}
</style>