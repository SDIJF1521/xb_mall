<template>
  <el-dialog 
    v-model="dialogVisible" 
    :title="title" 
    width="60%" 
    append-to-body
    :close-on-click-modal="false"
  >
    <CommodityViewDetails :commodity="currentCommodity" />
  </el-dialog>
 <el-table :data="commodity_list" ref="table" >
  <el-table-column type="selection"  width="55" />
  <el-table-column prop="id" label="商品id"/>
  <el-table-column prop="name" label="商品名称"/>
  <el-table-column prop="audit" label="商品状态">
    <template #default="scope">
      <el-tag :type="scope.row.audit === 1 ? 'primary' : scope.row.audit === 0 ? 'warning' : scope.row.audit === 3 ? 'danger' : 'danger'">
        {{ scope.row.audit === 1 ? '审核通过' : scope.row.audit === 0 ? '待审核' : scope.row.audit === 3 ? '已下架' : '审核未通过' }}
      </el-tag>
    </template>
  </el-table-column>
  <el-table-column prop="time" label="创建时间"/>
  <el-table-column align="right">
    <template #header>
      <el-input 
        v-model="search" 
        size="small" 
        placeholder="搜索商品名称" 
        clearable
        @input="handleSearch"
        @clear="handleSearchClear"
      />
    </template>
    <template #default="scope">
      <el-button type="primary" size="small">修改</el-button>
      <el-button type="info" size="small" @click="view_details(scope.row)">查看详情</el-button>
      <el-button v-if="scope.row.audit === 1" type="warning" size="small">下架</el-button>
      <el-button v-if="scope.row.audit === 3" type="success" size="small">上架</el-button>
      <el-button type="danger" size="small">删除</el-button>
    </template>
  </el-table-column>
 </el-table>
 <div style="display: flex; justify-content: center; margin-top: 20px;">
  <el-pagination 
    v-model:current-page="currentPage"
    :page-size="20" 
    :total="total" 
    @current-change="handleCurrentChange" 
  />
 </div>


</template>
<script setup lang="ts">
import {ref,onMounted,} from 'vue'
import axios  from 'axios';
import { useRoute } from 'vue-router'
import CommodityViewDetails from './commodity_view_details.vue'

const route = useRoute()
const id = ref(route.params.id)
const search = ref('')
const select = ref<Commodity[]>([])
const currentPage = ref(1)

const total = ref(0)
let searchTimer: ReturnType<typeof setTimeout> | null = null
const dialogVisible = ref(false)
const title = ref('')
const currentCommodity = ref<Commodity | null>(null)


interface Commodity {
  id: number
  name: string
  mg_list?: string[]
  img_list?: string[]
  info: string
  specification_list?: any[]
  types?: string[]
  classify_categorize?: string | number
  description?: string
  audit: number
  time: string
}

const commodity_list = ref<Commodity[]>([])

const token= ref(localStorage.getItem('buyer_access_token') || '')


const Axios = axios.create({
  baseURL:"http://127.0.0.1:8000/api"
})

defineOptions({
    name: 'CommodityList',
})

async function getCommodityList(page: number, selectValue?: string) {
  const params: any = {
    stroe_id: id.value,
    page: page
  }
  
  // 如果有搜索关键词，添加到参数中
  if (selectValue && selectValue.trim()) {
    params.select = selectValue.trim()
  }
  
  const res = await Axios.get('/buyer_get_commoidt', {
    params: params,
    headers: {
      'access-token': token.value
    }
  })
  
  if (res.status == 200) {
    if (res.data.success) {
      commodity_list.value = res.data.data
      total.value = res.data.page
    }
  }
}

// 查看详情
function view_details(data: Commodity) {
  currentCommodity.value = data
  dialogVisible.value = true
  title.value = '商品详情'
}
// 搜索处理函数（带防抖）
function handleSearch() {
  // 清除之前的定时器
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  
  // 设置新的定时器，500ms 后执行搜索
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    getCommodityList(1, search.value)
  }, 500)
}

function handleSearchClear() {
  currentPage.value = 1
  getCommodityList(1)
}

onMounted(async () => {
  await getCommodityList(1)
})

function handleCurrentChange(val: number) {
  currentPage.value = val
  getCommodityList(val, search.value)
}

</script>
