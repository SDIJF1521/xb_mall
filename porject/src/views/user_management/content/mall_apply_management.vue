<template>
  <div class="apply-page">
    <div class="apply-toolbar">
      <el-input
        v-model="searchKeyword"
        class="apply-search"
        placeholder="搜索用户名或名称"
        :prefix-icon="Search"
        clearable
        @input="handleSearch"
        @clear="handleSearch"
      />
    </div>
    <el-card class="list-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="mall_apply"
        stripe
        class="um-table"
        :row-key="applyRowKey"
        :header-cell-style="tableHeaderStyle"
        :row-style="{ height: '44px' }"
        @row-click="onApplyRowClick"
      >
        <template #empty>
          <el-empty description="暂无申请" />
        </template>
        <el-table-column label="申请名称" min-width="280">
          <template #default="{ row }">
            <span class="cell-apply">
              <el-icon class="cell-apply__icon"><Document /></el-icon>
              <span class="cell-apply__text">{{ row[0] }}</span>
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="skip(String(row[0]))">审核</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    <div v-if="total > 0" class="apply-pager">
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
</template>
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { Search, Document } from '@element-plus/icons-vue'
import router from '@/router';

const tableHeaderStyle = {
  background: 'var(--el-fill-color-light)',
  color: 'var(--el-text-color-regular)',
  fontWeight: '600',
};

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

function applyRowKey(row: ApplyItem) {
  return String(row[0]);
}

function onApplyRowClick(row: ApplyItem) {
  skip(String(row[0]));
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
.apply-page {
  width: 100%;
  max-width: 100%;
}
.apply-toolbar {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 10px;
}
.apply-search {
  width: min(320px, 100%);
}
.apply-search :deep(.el-input__wrapper) {
  border-radius: 20px;
}
.list-card {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
  overflow: hidden;
}
.list-card :deep(.el-card__body) {
  padding: 0;
}
.um-table {
  cursor: pointer;
}
.um-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}
.um-table :deep(.el-table__row:hover) {
  background-color: var(--el-fill-color-light) !important;
}
.cell-apply {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.cell-apply__icon {
  font-size: 18px;
  color: var(--el-color-primary);
}
.cell-apply__text {
  font-weight: 500;
}
.apply-pager {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>