<template>
  <!-- 查看详情对话框 -->
  <el-dialog 
    v-model="dialogVisible" 
    :title="title" 
    width="60%" 
    append-to-body
    :close-on-click-modal="false"
  >
    <CommodityViewDetails :commodity="currentCommodity" />
  </el-dialog>
  
  <!-- 编辑商品对话框 -->
  <el-dialog 
    v-model="editDialogVisible" 
    title="编辑商品" 
    width="80%" 
    append-to-body
    :close-on-click-modal="false"
    @opened="handleEditDialogOpened"
  >
    <CommodityEdit 
      v-if="currentCommodity"
      :key="`edit-${currentCommodity.id}`"
      :commodity="currentCommodity" 
      @cancel="handleEditCancel"
      @success="handleEditSuccess"
    />
  </el-dialog>

  <!-- 删除商品对话框 -->
  <el-dialog 
    v-model="deleteDialogVisible" 
    title="删除商品" 
    width="500px" 
    append-to-body
    :close-on-click-modal="false"
  >
    <CommodityDelete 
      v-if="currentCommodity"
      :commodity-id="currentCommodity.id"
      @cancel="handleDeleteCancel"
      @success="handleDeleteSuccess"
    />
  </el-dialog>

  <!-- 下架商品对话框 -->
  <el-dialog 
    v-model="delistingDialogVisible" 
    title="下架商品" 
    width="500px" 
    append-to-body
    :close-on-click-modal="false"
  >
    <CommodityDelisting 
      v-if="currentCommodity"
      :commodity-id="currentCommodity.id"
      @cancel="handleDelistingCancel"
      @success="handleDelistingSuccess"
    />
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
      <el-button type="primary" size="small" @click="edit_commodity(scope.row)">修改</el-button>
      <el-button type="info" size="small" @click="view_details(scope.row)">查看详情</el-button>
      <el-button v-if="scope.row.audit === 1" type="warning" size="small" @click="delisting_commodity(scope.row)">下架</el-button>
      <el-button v-if="scope.row.audit === 3" type="success" size="small">上架</el-button>
      <el-button type="danger" size="small" @click="delete_commodity(scope.row)">删除</el-button>
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
import CommodityEdit from './commodity_edit.vue'
import CommodityDelete from './commodity_delete.vue'
import CommodityDelisting from './commodity_delisting.vue'

const route = useRoute()
const id = ref(route.params.id)
const search = ref('')
const select = ref<Commodity[]>([])
const currentPage = ref(1)

const total = ref(0)
let searchTimer: ReturnType<typeof setTimeout> | null = null
const dialogVisible = ref(false)
const editDialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const delistingDialogVisible = ref(false)
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
    components: {
      CommodityViewDetails,
      CommodityEdit,
      CommodityDelete,
      CommodityDelisting
    }
})

async function getCommodityList(page: number, selectValue?: string) {
  const params: any = {
    stroe_id: id.value,
    page: page
  }
  
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

// 编辑商品
function edit_commodity(data: Commodity) {
  // 深拷贝商品数据，避免引用问题
  currentCommodity.value = {
    ...data,
    types: data.types ? [...data.types] : [],
    img_list: data.img_list ? [...data.img_list] : [],
    specification_list: data.specification_list ? data.specification_list.map((item: any) => ({
      ...item,
      specs: item.specs ? [...item.specs] : []
    })) : []
  }
  editDialogVisible.value = true
}

// 对话框打开时的处理
function handleEditDialogOpened() {
  // 对话框打开时，确保数据已正确传递
  // watch会自动触发初始化
}

// 取消编辑
function handleEditCancel() {
  editDialogVisible.value = false
  // 延迟清空，确保对话框关闭动画完成
  setTimeout(() => {
    currentCommodity.value = null
  }, 300)
}

// 编辑成功
function handleEditSuccess() {
  editDialogVisible.value = false
  currentCommodity.value = null
  // 刷新商品列表
  getCommodityList(currentPage.value, search.value)
}

// 删除商品
function delete_commodity(data: Commodity) {
  currentCommodity.value = data
  deleteDialogVisible.value = true
}

// 取消删除
function handleDeleteCancel() {
  deleteDialogVisible.value = false
  setTimeout(() => {
    currentCommodity.value = null
  }, 300)
}

// 删除成功
function handleDeleteSuccess() {
  deleteDialogVisible.value = false
  // 如果详情对话框正在显示被删除的商品，也关闭它
  if (dialogVisible.value && currentCommodity.value) {
    dialogVisible.value = false
  }
  currentCommodity.value = null
  // 刷新商品列表
  getCommodityList(currentPage.value, search.value)
}

// 下架商品
function delisting_commodity(data: Commodity) {
  currentCommodity.value = data
  delistingDialogVisible.value = true
}

// 取消下架
function handleDelistingCancel() {
  delistingDialogVisible.value = false
  setTimeout(() => {
    currentCommodity.value = null
  }, 300)
}

// 下架成功
function handleDelistingSuccess() {
  delistingDialogVisible.value = false
  currentCommodity.value = null
  // 刷新商品列表
  getCommodityList(currentPage.value, search.value)
}

function handleSearch() {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  
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
