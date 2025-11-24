<template>
    <el-dialog
    v-model="dialogVisible"
    :title="dialog_title"
    append-to-body
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
  </el-dialog>
  <el-table
    ref="multipleTableRef"
    :data="tableData"
    style="height: 80%;"
    @selection-change="handleSelectionChange"
  >
    <el-table-column type="selection" width="55" />
    <el-table-column prop="authority" label="ID" ></el-table-column>
    <el-table-column prop="role" label="权限标识" ></el-table-column>
    <el-table-column prop="name" label="权限名称" ></el-table-column>
    <el-table-column align="right"min-width="100">
       <template #header>
        <el-row :gutter="5">
          <el-col :span="10">
            <el-input v-model="search" size="small" placeholder="Type to search"/>
          </el-col>
          <el-col :span="4">
            <el-button
              size="small"
              type="primary"
              >
                新增
            </el-button>
          </el-col>
          <el-col :span="4">
            <el-button
              size="small"
              type="danger"
              :disabled="multipleSelection.length === 0"
              >
                批量删除
            </el-button>
          </el-col>
        </el-row>
      </template>
      <template #default="scope" type="">

        <el-button size="small"
          type="primary"
          :disabled = "scope.row.id === null"
        >
          修改
        </el-button>

        <el-button
          size="small"
          type="danger"
          :disabled = "scope.row.id === null"
        >
          删除
        </el-button>
      </template>
    </el-table-column>

   </el-table>
</template>
<script setup lang="ts">
import {ref,onMounted} from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios';

defineOptions({
  name: 'RoleListMain'
})

const Axios = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
});

const token = ref(localStorage.getItem('buyer_access_token')||'')
const route = useRoute().params
const mall_id = ref(route.id)

const search = ref('')
const dialogVisible = ref(false)
const dialog_title = ref('新增角色')

interface Role {
  id?: number
  name: string
  authority: number
  role: string
}

const tableData = ref<Role[]>([])

onMounted(async ()=>{
  const formdata = new FormData()
  formdata.append('token',token.value)
  formdata.append('stroe_id',mall_id.value.toString())

  const res = await Axios.post('/buyer_get_role',formdata)
  if(res.data.code === 200){
    if(res.data.data){
      // 解析后端返回的数据格式
      // 数据格式: [{"0": ["user", "用户"]}, {"1": ["root", "超级管理员"]}, ...]
      tableData.value = res.data.data.map((item: any) => {
        const authority = parseInt(Object.keys(item)[0]) // 获取键名作为authority
        const roleData = Object.values(item)[0] as string[] // 获取数组值
        return {
          authority: authority,
          id: roleData[2],
          role: roleData[0], // 权限标识，如 "user", "root"
          name: roleData[1]  // 权限名称，如 "用户", "超级管理员"
        }
      })
    }
  }
})

const multipleSelection = ref<Role[]>([])
const handleSelectionChange = (val: Role[]) => {
  multipleSelection.value = val
  console.log('选择变化:', val)
  console.log('选中权限:', val.map(role => role.name))
}
</script>
