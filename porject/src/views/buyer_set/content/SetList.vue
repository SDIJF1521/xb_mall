<template>
<el-row>
  <el-col :span="12">
    <el-button type="info" size="large" @click="exitLogin">退出登录</el-button>
  </el-col>
  <el-col :span="6">
    <el-button type="primary" size="large" @click="backToUser">回到用户端</el-button>
  </el-col>
</el-row>
</template>
<script setup lang="ts">
import {ref,onMounted} from 'vue'
import axios from 'axios'
import router from '@/router'
import { ElMessage } from 'element-plus'

defineOptions({name:'SetList'})

// 创建axios实例
const Axios = axios.create({
  baseURL:'http://127.0.0.1:8000/api'
})

const token = localStorage.getItem('buyer_access_token') || ''

// 退出登录
const exitLogin = ref(async ()=>{
  const res = await Axios.post('/buter_exit',{},{headers:{'Access-Token':token}})
  if (res.status == 200){
    if (res.data.current){
      localStorage.removeItem('buyer_access_token')
      ElMessage.success(res.data.msg)
      router.push('/buyer_sing')
    } else {
      ElMessage.error(res.data.msg)
    }
  } else {
    ElMessage.error(res.data.msg)
  }
})

// 回到用户端
const backToUser = ref(()=>{
  router.push('/')
})

</script>
