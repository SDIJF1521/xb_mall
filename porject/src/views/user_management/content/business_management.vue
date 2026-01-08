<template>
    <div style="display: flex; justify-content: center; margin-top: 20px; margin-bottom: 40px;">
        <el-input
            v-model="searchKeyword"
            style="width: 240px; border-radius: 20px;"
            placeholder="搜索店铺ID或卖家名字"
            :prefix-icon="Search"
            clearable
            @input="handleSearch"
            @clear="handleSearch"
        />
    </div>
    <div v-if="management_list.length == 0">
        <el-empty description="暂无数据" />
    </div>
    <div v-else>
        <div v-for="itrm in management_list" :key="itrm" style="margin-bottom: 10px;">
            <el-card shadow="hover" @click="skip(itrm)" style="width: 100%; text-align: center; cursor: pointer;">
                <span class="card-text">{{ itrm }}</span>
            </el-card>
        </div>
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
:deep(.el-input__wrapper) {
  border-radius: 20px;
}

.card-text {
  transition: color 0.3s ease;
}

.el-card:hover .card-text {
  background-image: linear-gradient(to right, #ec8e8c, #8556ab);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  -webkit-text-fill-color: transparent;
}
</style>