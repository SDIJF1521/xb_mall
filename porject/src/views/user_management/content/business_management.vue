<template>
  <div class="biz-page">
    <div class="biz-toolbar">
      <el-input
        v-model="searchKeyword"
        class="biz-search"
        placeholder="搜索店铺ID或卖家名字"
        :prefix-icon="Search"
        clearable
        @input="handleSearch"
        @clear="handleSearch"
      />
    </div>
    <el-card v-if="management_list.length === 0" class="biz-card" shadow="never">
      <el-empty description="暂无数据" />
    </el-card>
    <template v-else>
      <el-card class="biz-card biz-list" shadow="never">
        <div v-for="itrm in management_list" :key="String(itrm)" class="biz-row" @click="skip(itrm)">
          <span class="card-text">{{ itrm }}</span>
        </div>
      </el-card>
      <div class="biz-pager">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="5"
          :pager-count="11"
          layout="prev, pager, next"
          :total="total"
          @current-change="handleCurrentChange"
        />
      </div>
    </template>
  </div>
</template>
<script setup lang="ts">
import axios from 'axios';
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Search } from '@element-plus/icons-vue';

const Axios = axios.create({
    baseURL:'http://127.0.0.1:8000/api'
})
const total = ref(0) // 总记录数
const currentPage = ref(1) // 当前页码
const management_list = ref<any[]>([])
const searchKeyword = ref('')
let searchTimer: ReturnType<typeof setTimeout> | null = null

defineOptions({
    name:'BusinessManagement'
})

// 防抖搜索函数
function handleSearch() {
    if (searchTimer) {
        clearTimeout(searchTimer)
    }
    // 搜索时重置到第一页
    currentPage.value = 1
    // 如果搜索框为空，立即请求所有数据
    if (!searchKeyword.value || !searchKeyword.value.trim()) {
        request(1)
        return
    }
    // 否则使用防抖延迟
    searchTimer = setTimeout(() => {
        request(1)
    }, 500) // 500ms 防抖延迟
}

async function request(page_number:number=1) {
    try {
        const token = localStorage.getItem('admin_access_token')||''
        const fromdata = new FormData()
        fromdata.append('token',token)
        fromdata.append('page',String(page_number))
        // 如果有搜索关键词，添加到请求中
        if (searchKeyword.value && searchKeyword.value.trim()) {
            fromdata.append('select', searchKeyword.value.trim())
        }
        await Axios.post('/number_merchants',fromdata)
        .then((res)=>{
            if (res.data.current) {
                management_list.value = Object.values(res.data.merchant_list)
                total.value = res.data.page || 0
                currentPage.value = res.data.current_page || page_number
            } else {
                ElMessage.error(res.data.msg || '获取数据失败')
                management_list.value = []
                total.value = 0
                currentPage.value = 1
            }
        })
        .catch((error) => {
            console.error('请求失败:', error)
            ElMessage.error('请求失败，请稍后重试')
            management_list.value = []
            total.value = 0
            currentPage.value = 1
        })
    } catch (error) {
        console.error('请求异常:', error)
        ElMessage.error('请求异常，请稍后重试')
    }
}

function skip(name:string){
    window.location.href = `/business_management/${name}`
} 

async function handleCurrentChange(val:number){
    currentPage.value = val
    await request(val)
}

onMounted(async ()=>{
    await request()
})
</script>

<style scoped>
.biz-page {
  width: 100%;
}
.biz-toolbar {
  margin-bottom: 10px;
}
.biz-search {
  width: min(320px, 100%);
}
.biz-search :deep(.el-input__wrapper) {
  border-radius: 20px;
}
.biz-card {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
}
.biz-list :deep(.el-card__body) {
  padding: 0;
}
.biz-row {
  padding: 11px 14px;
  cursor: pointer;
  border-bottom: 1px solid var(--el-border-color-lighter);
  text-align: center;
  transition: background 0.15s;
}
.biz-row:last-child {
  border-bottom: none;
}
.biz-row:hover {
  background: var(--el-fill-color-light);
}
.biz-pager {
  display: flex;
  justify-content: center;
  margin-top: 12px;
}
.card-text {
  font-weight: 500;
}
</style>