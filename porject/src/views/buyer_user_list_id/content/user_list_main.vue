<template>
  <!-- 弹窗 -->
  <el-dialog
    v-model="dialogVisible"
    :title="dialog_title"
    append-to-body
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
    <component :is="mod" @child-event="handleEvent"/>

  </el-dialog>
   <el-table
    ref="multipleTableRef"
    :data="tableData"
    row-key="id"
    style="height: 80%;"
    @selection-change="handleSelectionChange"

  >
    <el-table-column type="selection" width="55" />
    <el-table-column prop="img" label="用户头像" >
      <template #default="scope">
        <el-avatar :src="scope.row.img" fit="fill" :preview-src-list="[scope.row.img]"  size = 'small'/>
      </template>
    </el-table-column>
    <el-table-column prop="user" label="用户名" ></el-table-column>
    <el-table-column prop="password" label="密码" ></el-table-column>
    <el-table-column prop="authority" label="用户权限" >
      <template #default="scope">
        <el-tag :type="scope.row.authority === 0 ? 'primary' : scope.row.authority === 1 ? 'success' : 'danger'">
          {{ scope.row.authority === 0 ? '普通用户' : scope.row.authority === 1 ? '管理员' : '超级管理员' }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="email" label="邮箱" min-width="200"></el-table-column>
    <el-table-column align="right">
       <template #header>
        <el-row :gutter="10">
          <el-col :span="16">
            <el-input v-model="search" size="small" placeholder="Type to search" />
          </el-col>
          <el-col :span="4">
            <el-button
              size="small"
              type="primary"
              @click="Add_button_click" >
                Add
            </el-button>
          </el-col>
        </el-row>
      </template>
      <template #default="scope" type="">

        <el-button size="small"
        >
          Edit
        </el-button>

        <el-button
          size="small"
          type="danger"

        >
          Delete
        </el-button>
      </template>
    </el-table-column>

   </el-table>
</template>
<script setup lang="ts">
import {ref,onMounted} from 'vue'
import axios from 'axios'
import { useRoute } from 'vue-router'
import type { TableInstance } from 'element-plus'
import AddUser from '@/views/buyer_user_list_id/content/add_user.vue'

defineOptions({
    name: 'UserListMain',
    components: {
        AddUser
    }
})

const route = useRoute().params

const Axios = axios.create({
   baseURL: "http://127.0.0.1:8000/api"
})

interface User {
  id: number
  user: string
  password: string
  authority:number
  img:string
  email:string

}

const token = localStorage.getItem('buyer_access_token')
const mod = ref('AddUser')
const search = ref('')
const dialog_title = ref('')

const multipleTableRef = ref<TableInstance>()
const multipleSelection = ref<User[]>([])
const dialogVisible = ref(false)

const handleEvent = (data:boolean)=>{
   dialogVisible.value = data
}

const id =  ref(route.id)
const handleSelectionChange = (val: User[]) => {
  multipleSelection.value = val
}
const tableData = ref<User[]>([

])

onMounted(async ()=>{
  try{
    const formdata = new FormData()
    formdata.append('token',token||'')
    formdata.append('id',id.value.toString())
    const res = await Axios.post('buyer_mall_user_list',formdata)

    // 验证响应数据结构
    if(res.data && res.data.code === 200){
      if (res.data.current === true && Array.isArray(res.data.data)){
        tableData.value = res.data.data
      } else {
        console.warn('API返回数据格式异常:', res.data)
        tableData.value = []
      }
    } else {
      console.error('API请求失败:', res?.data?.msg || '未知错误')
      tableData.value = []
    }
  }catch(error){
    console.error('获取用户列表失败:', error)
    tableData.value = []
  }
})

const deleteSelectedUsers = () => {
  console.log(multipleSelection.value);

}

function Add_button_click(){
  dialog_title.value = '新增用户'
  dialogVisible.value = true
  mod.value = 'AddUser'
}

</script>
