<template>
  <!-- 弹窗 -->
  <el-dialog
    v-model="dialogVisible"
    :title="dialog_title"
    append-to-body
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :modal-append-to-body="false"
    custom-class="user-dialog"
  >
    <component :is="mod"/>

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
    <el-table-column prop="name" label="用户名" ></el-table-column>
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
import type { TableInstance } from 'element-plus'
import AddUser from '@/views/buyer_user_list/content/add_user.vue'

defineOptions({
    name: 'UserListMain',
    components: {
        AddUser
    }
})

interface User {
  id: number
  name: string
  password: string
  authority:number
  img:string
  email:string

}
const mod = ref('AddUser')
const search = ref('')
const dialog_title = ref('')

const multipleTableRef = ref<TableInstance>()
const multipleSelection = ref<User[]>([])
const dialogVisible = ref(false)
const toggleSelection = (rows?: User[], ignoreSelectable?: boolean) => {
  if (rows) {
    rows.forEach((row) => {
      multipleTableRef.value!.toggleRowSelection(
        row,
        undefined,
        ignoreSelectable
      )
    })
  } else {
    multipleTableRef.value!.clearSelection()
  }
}
const handleSelectionChange = (val: User[]) => {
  multipleSelection.value = val
}
const tableData: User[] = [
  {
    id: 1,
    name: '用户1',
    password: '123456',
    authority: 0,
    img: 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
    email:'123@qq.com'
  },{
    id: 2,
    name: '用户2',
    password: '123456',
    authority: 1,
    img: 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
    email:'123@qq.com'

  },{
    id: 3,
    name: '用户3',
    password: '123456',
    authority: 2,
    img: 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
    email:'123@qq.com'
  }
]

const deleteSelectedUsers = () => {
  console.log(multipleSelection.value);

}

function Add_button_click(){
  dialog_title.value = '新增用户'
  dialogVisible.value = true
  mod.value = 'AddUser'
}

</script>

<style scoped>
/* 对话框样式优化 */
:deep(.user-dialog) {
  z-index: 2000 !important;
}

:deep(.el-dialog__wrapper) {
  z-index: 2001 !important;
}
</style>
