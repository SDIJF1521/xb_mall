<template>
  <!-- 弹窗 -->
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
    v-if="mod === 'AddUser'"
  />
  <component
    :is="mod"
    @child-event="handleEvent"
    v-else-if="mod === 'ChangeUser' && selectedUser"
    :name="selectedUser.user"
    :password="selectedUser.password"
    :authority="Number(selectedUser.authority)"
    :img="selectedUser.img"
    :email="selectedUser.email"
  />

  </el-dialog>
   <el-table
    ref="multipleTableRef"
    :data="tableData"
    style="height: 80%;"
    @selection-change="handleSelectionChange"
  >
    <el-table-column type="selection" width="55" />
    <el-table-column prop="img" label="用户头像" >
      <template #default="scope">
        <el-avatar :src="'data:image/png;base64,'+scope.row.img" fit="fill" :preview-src-list="[scope.row.img]"  size = 'small'/>
      </template>
    </el-table-column>
    <el-table-column prop="user" label="用户名" ></el-table-column>
    <el-table-column prop="password" label="密码" ></el-table-column>
    <el-table-column prop="authority" label="用户权限" >
      <template #default="scope">
        <el-tag :type="getAuthorityTagType(scope.row.authority)">
          {{ getAuthorityName(scope.row.authority)[1] }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="email" label="邮箱" min-width=""></el-table-column>
    <el-table-column align="right"min-width="100">
       <template #header>
        <el-row :gutter="5">
          <el-col :span="10">
            <el-input v-model="search" size="small" placeholder="Type to search"  @keyup.enter="select_fun"/>
          </el-col>
          <el-col :span="4">
            <el-button
              size="small"
              type="primary"
              @click="Add_button_click" >
                新增
            </el-button>
          </el-col>
          <el-col :span="4">
            <el-button
              size="small"
              type="danger"
              :disabled="multipleSelection.length === 0"
              @click="deleteSelectedUsers" >
                批量删除
            </el-button>
          </el-col>
        </el-row>
      </template>
      <template #default="scope" type="">

        <el-button size="small"
          type="primary"
          @click="Change_button_click(scope.row)"
        >
          修改
        </el-button>

        <el-button
          size="small"
          type="danger"
          @click="delete_user_commit(scope.row.user)"
        >
          删除
        </el-button>
      </template>
    </el-table-column>

   </el-table>
</template>
<script setup lang="ts">
import {ref,onMounted,computed} from 'vue'
import axios from 'axios'
import { useRoute } from 'vue-router'
import type { TableInstance } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import AddUser from '@/views/buyer_user_list_id/content/add_user.vue'
import ChangeUser from '@/views/buyer_user_list_id/content/change_user.vue'

defineOptions({
    name: 'UserListMain',
    components: {
        AddUser,
        ChangeUser
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

interface RoleOption {
  id: number
  name: string
}

const token = localStorage.getItem('buyer_access_token')
const mod = ref('AddUser')
const search = ref('')
const dialog_title = ref('')
const selectedUser = ref<User | null>(null)
const roleOptions = ref<RoleOption[]>([])

const multipleTableRef = ref<TableInstance>()
const multipleSelection = ref<User[]>([])
const dialogVisible = ref(false)

// 获取权限标签类型
const getAuthorityTagType = (authority: number): string => {

  const role = roleOptions.value.find(role => role.id === authority)
  if (!role) return 'info'

  // 根据权限名称返回对应的标签类型
  if (role.name[1].includes('超级')) return 'danger'
  if (role.name[1].includes('管理')) return 'success'
  return 'primary'
}

// 获取权限名称
const getAuthorityName = (authority: number): string => {
  const role = roleOptions.value.find(role => role.id === authority)
  return role ? role.name : '未知权限'
}

// 获取权限列表
const fetchRoleList = async () => {
  try {
    const role_formdata = new FormData()
    role_formdata.append('token', token || '')
    role_formdata.append('stroe_id', id.value?.toString() || '')

    const response = await Axios.post('/buyer_get_role', role_formdata)

    if (response.data.code === 200 && response.data.data) {
      // 将后端返回的权限数据转换为前端需要的格式
      roleOptions.value = response.data.data.map((role: any) => {
        const roleId = Object.keys(role)[0]
        const roleName = Object.values(role)[0]
        return {
          id: parseInt(roleId),
          name: roleName as string
        }
      })
    } else {
      console.warn('获取权限列表失败，使用默认权限选项')
      // 如果获取失败，使用默认权限选项
      roleOptions.value = [
        { id: 0, name: '普通用户' },
        { id: 1, name: '管理员' },
        { id: 2, name: '超级管理员' }
      ]
    }
  } catch (error) {
    console.error('获取权限列表失败:', error)
    // 错误时使用默认权限选项
    roleOptions.value = [
      { id: 0, name: '普通用户' },
      { id: 1, name: '管理员' },
      { id: 2, name: '超级管理员' }
    ]
  }
}

const handleEvent = async (data:boolean)=>{
   dialogVisible.value = data
   // 当对话框关闭时，重新加载用户列表
   if (!data) {
     await all_user_list()
   }
}

const id =  ref(route.id)
const handleSelectionChange = (val: User[]) => {
  multipleSelection.value = val
  console.log('选择变化:', val)
  console.log('选中用户:', val.map(user => user.user))
}
const tableData = ref<User[]>([

])


async function all_user_list(){
  try{
    const formdata = new FormData()
    formdata.append('token',token||'')
    formdata.append('id',id.value.toString())
    const res = await Axios.post('/buyer_mall_user_list',formdata)

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
}


onMounted(async ()=>{
  // 先获取权限列表，再获取用户列表
  await fetchRoleList()
  await all_user_list()
})

const deleteSelectedUsers = async() => {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning('请先选择要删除的用户')
    return
  }

  try {
    // 显示确认对话框
    await ElMessageBox.confirm(
      `确定要删除选中的 ${multipleSelection.value.length} 个用户吗？此操作不可恢复。`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        center: true
      }
    )

    // 用户确认删除后执行删除操作
    const formdata = new FormData()
    formdata.append('token',token||'')
    formdata.append('strore_id',id.value.toString())
    multipleSelection.value.forEach(user => {
      formdata.append('user_name', user.user); // 每个用户名单独 append，key 都是 user_name
    });
    const res = await Axios.delete('/buyer_user_delete',{data:formdata})

    if (res.status == 200){
      if (res.data.current){
        ElMessage.success('批量删除用户成功')
        // 删除成功后重新加载用户列表
        await all_user_list()
      }else{
        ElMessage.error('批量删除用户失败')
      }
    }else{
      ElMessage.error('批量删除用户失败')
    }
  } catch (error) {
    // 用户点击取消或删除失败
    if (error !== 'cancel') {
      console.error('批量删除用户失败:', error)
      ElMessage.error('批量删除用户失败')
    } else {
      ElMessage.info('已取消批量删除操作')
    }
  }
}

function Add_button_click(){
  dialog_title.value = '新增用户'
  dialogVisible.value = true
  mod.value = 'AddUser'
}

async function select_fun(){
  if (search.value==''){
    await all_user_list()
    return
  }else{
    const select_formdata = new FormData()
    select_formdata.append('token',token||'')
    select_formdata.append('strore_id',id.value.toString())
    select_formdata.append('user_name',search.value)
    const res = await Axios.post('/buyer_user_select',select_formdata)
    try{
      if (res.status == 200){
        if (res.data.current){
          tableData.value = res.data.data
        }else{
          tableData.value = []
        }
      }else{
        tableData.value = []
      }
    }catch{
     ElMessage.error('查询用户失败')
    }
  }
}

async function delete_user_commit(user:string){
  try {
    // 显示确认对话框
    await ElMessageBox.confirm(
      `确定要删除用户 "${user}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        center: true
      }
    )

    // 用户确认删除后执行删除操作
    const delete_user_formdata = new FormData()
    delete_user_formdata.append('token',token||'')
    console.log(id);

    delete_user_formdata.append('strore_id',id.value.toString())
    delete_user_formdata.append('user_name',user)

    const res = await Axios.delete('/buyer_user_delete',{data:delete_user_formdata})

    if (res.status == 200){
      if (res.data.current){
        ElMessage.success('删除用户成功')
        // 删除成功后重新加载用户列表
        await all_user_list()
      }else{
        ElMessage.error('删除用户失败')
      }
    }else{
      ElMessage.error('删除用户失败')
    }
  } catch (error) {
    // 用户点击取消或删除失败
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error('删除用户失败')
    } else {
      ElMessage.info('已取消删除操作')
    }
  }
}

function Change_button_click(user?: User){
  dialog_title.value = '修改用户'
  selectedUser.value = user || null
  dialogVisible.value = true
  mod.value = 'ChangeUser'
}
</script>
