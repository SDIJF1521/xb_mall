<template>
 <el-table :data="commodity_list" ref="table" >
  <el-table-column type="selection"  width="55" />
  <el-table-column prop="id" label="商品id"/>
  <el-table-column prop="name" label="商品名称"/>
  <el-table-column prop="audit" label="商品状态">
    <template #default="scope">
      <el-tag :type="scope.row.audit === 1 ? 'primary' : 'danger'">
        {{ scope.row.audit === 1 ? '审核通过' : '审核未通过' }}
      </el-tag>
    </template>
  </el-table-column>
  <el-table-column prop="time" label="创建时间"/>
  <el-table-column align="right">
    <template #header>
      <el-input v-model="search" size="small" placeholder="Type to search" />
    </template>
    <template #default="scope">
      <el-button type="primary" size="small">修改</el-button>
      <el-button type="info" size="small">查看详情</el-button>
      <el-button type="danger" size="small">删除</el-button>
    </template>
  </el-table-column>
 </el-table>
 <div style="display: flex; justify-content: center; margin-top: 20px;">
  <el-pagination :page-size="20" :total="total" @current-change="handleCurrentChange" />
 </div>


</template>
<script setup lang="ts">
import {ref,onMounted,} from 'vue'
import axios  from 'axios';
import { useRoute } from 'vue-router'
import type { el } from 'element-plus/es/locales.mjs';

const route = useRoute()
const id = ref(route.params.id)
const search = ref('')
const select = ref<Commodity[]>([])

const total = ref(0)



interface Commodity {
  id: number
  name: string
  money: number
  stock: number
  description: string
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

async function getCommodityList(page: number) {
  const res = await Axios.get('/buyer_get_commoidt',{
    params:{
      stroe_id:id.value,
      page:page
    },
    headers:{
      'access-token': token.value
    }
  })
  if (res.status ==200){
    if (res.data.success){
      commodity_list.value = res.data.data
      total.value = res.data.page
    }
  }
}

onMounted(async () =>{
  await getCommodityList(1)
})

function handleCurrentChange(val: number) {
  getCommodityList(val)
}

</script>
