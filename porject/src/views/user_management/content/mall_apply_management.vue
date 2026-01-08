<template>
    <div class="list-container">
        <div style="display: flex; justify-content: center; margin-top: 20px; margin-bottom: 40px;">
            <el-input
                v-model="searchKeyword"
                style="width: 240px; border-radius: 20px;"
                placeholder="搜索用户名或名称"
                :prefix-icon="Search"
                clearable
                @input="handleSearch"
                @clear="handleSearch"
            />
        </div>
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="mall_apply.length > 0">
          <ul>
            <li v-for="(item, index) in mall_apply" :key="index" @click="skip(item[0])">{{ item[0] }}</li>
          </ul>
          <div style="display: flex; justify-content: center; margin-top: 20px;">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="5"
              :pager-count="11"
              layout="prev, pager, next"
              :total="total"
              @current-change="handleCurrentChange"
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
import { Search } from '@element-plus/icons-vue';
import router from '@/router';

const total = ref(0) // 总记录数
const currentPage = ref(1) // 当前页码
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
  current_page?: number;
}

const Axios = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
  });

const mall_apply = ref<ApplyItem[]>([]);
const loading = ref<boolean>(false);
const searchKeyword = ref('')
let searchTimer: ReturnType<typeof setTimeout> | null = null
let intervalId: number | undefined;

const checkToken = (): string => {
  const token = localStorage.getItem('admin_access_token');
  if (!token) {
    ElMessage.error('请先登录');
  }
  return token || '';
};

// 防抖搜索函数
function handleSearch() {
    if (searchTimer) {
        clearTimeout(searchTimer)
    }
    // 搜索时重置到第一页
    currentPage.value = 1
    // 如果搜索框为空，立即请求所有数据
    if (!searchKeyword.value || !searchKeyword.value.trim()) {
        fetchData(1)
        return
    }
    // 否则使用防抖延迟
    searchTimer = setTimeout(() => {
        fetchData(1)
    }, 500) // 500ms 防抖延迟
}

const skip = (id:string) =>{
  router.push({name:'AuditApplySeller',params:{id:id}})
}

const fetchData = async (page_number:number=1) => {
    try {
      const token = checkToken();
      if (!token) return;

      loading.value = true;
      const formdata = new FormData();
      formdata.append('token', token);
      formdata.append('page', String(page_number));
      // 如果有搜索关键词，添加到请求中
      if (searchKeyword.value && searchKeyword.value.trim()) {
          formdata.append('select', searchKeyword.value.trim())
      }
      const response = await Axios.post<ApiResponse>('/get_apply_seller_list', formdata);
      console.log(response.data);
      

      if (response.data.current && Array.isArray(response.data.apply_list)) {
        mall_apply.value = response.data.apply_list;
        total.value = response.data.page || 0;
        currentPage.value = response.data.current_page || page_number;
      } else {
        ElMessage.warning(response.data.msg || '获取数据失败');
        mall_apply.value = [];
        total.value = 0;
        currentPage.value = 1;
      }
    } catch (error) {
      console.error('请求失败', error);
      ElMessage.error('网络错误，无法获取数据');
      mall_apply.value = [];
      total.value = 0;
      currentPage.value = 1;
    } finally {
      loading.value = false;
    }
  };

async function handleCurrentChange(val:number){
    currentPage.value = val
    await fetchData(val)
}

onMounted(async() =>{
  // 立即执行一次
  await fetchData(1);
})

onUnmounted(() => {
  if (intervalId) {
    window.clearInterval(intervalId);
  }
  if (searchTimer) {
    clearTimeout(searchTimer);
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

:deep(.el-input__wrapper) {
  border-radius: 20px;
}
</style>