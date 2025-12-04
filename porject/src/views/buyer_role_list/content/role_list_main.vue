<template>
    <el-dialog
    v-model="dialogVisible"
    :title="dialog_title"
    append-to-body
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
    <component
    :is="mod"
    @child-event="handleEvent"
    v-if="mod === 'RoleAdd'"
  />
    <component
    :is="mod"
    @child-event="handleEvent"
    v-if="mod === 'ChangeRole'"
    :role_id="role_id"
  />
  </el-dialog>
  <el-table
    ref="multipleTableRef"
    :data="sortedTableData"
    style="height: 80%;"
    @selection-change="handleSelectionChange"
    row-key="role_id"
    :row-class-name="({row}: {row: Role}) => row.id === null ? 'disabled-row' : ''"
  >
    <el-table-column type="selection" width="55" :selectable="(row: Role) => row.id !== null" />
    <el-table-column prop="role_id" label="ID" ></el-table-column>
    <el-table-column prop="role" label="权限标识" ></el-table-column>
    <el-table-column prop="name" label="权限名称" ></el-table-column>
    <el-table-column align="right"min-width="100">
       <template #header>
        <el-row :gutter="5">
          <el-col :span="10">
            <el-input v-model="search" @keyup.enter="select_role" size="small" placeholder="Type to search"/>
          </el-col>
          <el-col :span="4">
            <el-button
              size="small"
              type="primary"
              @click="Add"
              >
                新增
            </el-button>
          </el-col>
          <el-col :span="4">
            <el-button
              size="small"
              type="danger"
              :disabled="multipleSelection.length === 0"
              @click="delete_roles"
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
          @click="Change(scope.row)"
        >
          修改
        </el-button>

        <el-button
          size="small"
          type="danger"
          :disabled = "scope.row.id === null"
          @click="delete_role(scope.row)"
        >
          删除
        </el-button>
      </template>
    </el-table-column>

   </el-table>
</template>
<script setup lang="ts">
import {ref,onMounted,computed,nextTick} from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage,ElMessageBox } from 'element-plus'
import ChangeRole from './change_role.vue'
import RoleAdd from './role_add.vue'
import axios from 'axios';

const mod = ref('RoleAdd')
defineOptions({
  name: 'RoleListMain',
  components: { RoleAdd,
                ChangeRole}
})

const Axios = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
});

const token = ref(localStorage.getItem('buyer_access_token')||'')
const route = useRoute().params
const mall_id = ref<string>(Array.isArray(route.id) ? route.id[0] : route.id || '')

const search = ref('')
const dialogVisible = ref(false)
const dialog_title = ref('新增角色')
const role_id = ref(0)

interface Role {
  id?: number
  name: string
  role_id: number
  role: string
}

const tableData = ref<Role[]>([])

// 计算属性：按ID排序的数据
const sortedTableData = computed(() => {
  return [...tableData.value].sort((a, b) => (a.id || 0) - (b.id || 0))
})

async function all_role_list(){
  const formdata = new FormData()
  formdata.append('token',token.value)
  formdata.append('stroe_id',mall_id.value)
  try{
    const res = await Axios.post('/buyer_get_role',formdata)
    if(res.data.code === 200){
      if(res.data.data){
        const processedData = res.data.data.map((item: any) => {
          const keys = Object.keys(item)
          const values = Object.values(item) as string[][]

          if (keys.length === 0 || values.length === 0 || !Array.isArray(values[0]) || values[0].length < 3) {
            console.warn('Invalid data format:', item)
            return null
          }

          const role_id = parseInt(keys[0]) // 获取键名作为role_id
          const roleData = values[0] // 获取数组值
          return {
            role_id: role_id,
            id: roleData[2],
            role: roleData[0], // 权限标识，如 "user", "root"
            name: roleData[1]  // 权限名称，如 "用户", "超级管理员"
          }
        }).filter((item: any): item is Role => item !== null)
        tableData.value = processedData
      }
    }
  }catch (error){
    console.error('Error fetching role list:', error)
  }
}

onMounted(async ()=>{
  await all_role_list()
})

const multipleSelection = ref<Role[]>([])
const handleSelectionChange = (val: Role[]) => {
  multipleSelection.value = val
  console.log('选择变化:', val)
  console.log('选中权限:', val.map(role => role.name))
}

function Add(){
  dialog_title.value = '新增角色'
  mod.value = 'RoleAdd'
  dialogVisible.value = true
}

const handleEvent = async (data:boolean)=>{
   dialogVisible.value = data
   // 当对话框关闭时，重新加载用户列表并重置role_id
   if (!data) {
     role_id.value = 0 // 重置role_id
     await all_role_list()
   }
}

const select_role = ref(async ()=>{
  if (search.value.trim() === '') {
    await all_role_list()
    return
  }else{
    const formdata = new FormData()
    formdata.append('token',token.value)
    formdata.append('stroe_id',mall_id.value)
    formdata.append('select_data',search.value)
    try{
      const res = await Axios.post('/buyer_get_role',formdata)
      if(res.data.code === 200){
        if(res.data.data){
          const processedData = res.data.data.map((item: any) => {
            const keys = Object.keys(item)
            const values = Object.values(item) as string[][]

            if (keys.length === 0 || values.length === 0 || !Array.isArray(values[0]) || values[0].length < 3) {
              console.warn('Invalid data format:', item)
              return null
            }

            const role_id = parseInt(keys[0]) // 获取键名作为role_id
            const roleData = values[0] // 获取数组值
            return {
              role_id: role_id,
              id: roleData[2],
              role: roleData[0], // 权限标识，如 "user", "root"
              name: roleData[1]  // 权限名称，如 "用户", "超级管理员"
            }
          }).filter((item: any): item is Role => item !== null)
          tableData.value = processedData
        }
      }
    }catch (error){
      console.error('Error fetching role list:', error)
    }
  }
})


async function delete_role(val: Role){
  try {
    await ElMessageBox.confirm(
        `确定要删除角色 "${val.name}" 吗？此操作不可恢复。`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
          center: true
        }
      )
    console.log(val.role_id);


    const DeleteFromData = new FormData()
    DeleteFromData.append('token',token.value)
    DeleteFromData.append('stroe_id',mall_id.value)
    DeleteFromData.append('role_id',val.role_id.toString())
    const res = await Axios.delete('/buyer_role_delete',{data:DeleteFromData})
    if (res.status == 200){
      if (res.data.current){
        ElMessage.success('删除成功')
        await all_role_list()
      }else{
        ElMessage.error('删除失败')
      }
    }
  }catch (error) {
    // 用户点击取消或删除失败
    if (error !== 'cancel') {
      console.error('删除角色失败:', error)
      ElMessage.error('删除角色失败')
    } else {
      ElMessage.info('已取消删除操作')
    }
  }
}

async function delete_roles(){
  console.log(multipleSelection.value.map(item => item.role_id));
  try {
    await ElMessageBox.confirm(
        `确定要删除选中的 ${multipleSelection.value.length} 个角色吗？此操作不可恢复。`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
          center: true
        }
      )
    const DeleteFromData = new FormData()
    DeleteFromData.append('token',token.value)
    DeleteFromData.append('stroe_id',mall_id.value)
    multipleSelection.value.forEach(item => {
      DeleteFromData.append('role_id',item.role_id.toString())
    })
    const res = await Axios.delete('/buyer_role_delete',{data:DeleteFromData})
    if (res.status == 200){
      if (res.data.current){
        ElMessage.success('删除成功')
        await all_role_list()
      }else{
        ElMessage.error('删除失败')
      }
    }
  }catch (error) {
    // 用户点击取消或删除失败
    if (error !== 'cancel') {
      console.error('删除角色失败:', error)
      ElMessage.error('删除角色失败')
    } else {
      ElMessage.info('已取消删除操作')
    }
  }
}

function Change(val: Role){
  dialog_title.value = '修改角色'
  // 先设置role_id，再显示对话框，确保子组件能正确获取数据
  role_id.value = val.role_id
  mod.value = 'ChangeRole'
  // 使用nextTick确保role_id更新后再显示对话框
  nextTick(() => {
    dialogVisible.value = true
  })
}
</script>

<style scoped>
.disabled-row {
  opacity: 0.6;
  background-color: #f5f5f5;
}

.disabled-row:hover {
  opacity: 0.8;
}
</style>
