<template>
    <el-form
    ref="ruleFormRef"
    label-width="auto"
    :model="formData"
    :rules="rules"
  >
    <el-form-item label="权限名称" prop="role_name">
      <el-input v-model="formData.role_name" />
    </el-form-item>
    <el-form-item label="权限标识" prop="role">
      <el-input v-model="formData.role" />
    </el-form-item>
    <el-form-item label="操作组合" prop="execute_code">
        <el-checkbox-group v-model="formData.execute_code">
          <el-checkbox
            v-for="item in role_code_list"
            :key="Object.keys(item)[0]"
            :value="Number(Object.keys(item)[0])"
          >
            {{ Object.values(item)[0] }}
          </el-checkbox>
        </el-checkbox-group>
    </el-form-item>
  </el-form>
  <el-row :gutter="10">
    <el-col :span="12">
      <el-button size="small" type="primary" style="width: 100%;" @click="commit_form">提交</el-button>
    </el-col>
    <el-col :span="12">
      <el-button size="small" type="danger" style="width: 100%;" @click="close_dialog" >取消</el-button>
    </el-col>
  </el-row>
</template>
<script setup lang="ts">
import {ref,onMounted,reactive,watch} from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios';
import { sum } from 'element-plus/es/components/table-v2/src/utils.mjs';

defineOptions({
  name: 'ChangeRole',
})

const ruleFormRef = ref() // 修正：在setup中定义ref
const token = ref(localStorage.getItem('buyer_access_token'))
const route = useRoute()
const id = route.params.id
const role_code_list = ref([])
const Axios = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
});

interface FormData {
  role_name: string
  role:string
  execute_code?: number[]

}

const role_id = defineProps({
  role_id: {
    type: Number,
    default: 0
  }
})
const emit = defineEmits(['childEvent'])
const formData = ref<FormData>({
  role_name: '',
  role:'',
  execute_code: undefined
})

// 获取权限代码列表
async function fetchRoleCodeList() {
  const formdata = new FormData()
  formdata.append('token',token.value||'')
  const res = await Axios.post('/buyer_role_code_get',formdata)
  if (res.status == 200){
    if (res.data.current){
      console.log('权限代码列表:', res.data.data);
      role_code_list.value = res.data.data
    }
  }
}

// 重置表单
function resetForm() {
  formData.value = {
    role_name: '',
    role: '',
    execute_code: undefined
  }
}

// 获取角色信息
async function fetchRoleInfo() {
  if (!role_id.role_id) return

  // 先重置表单
  resetForm()

  const res_info = await Axios.get('/buyer_role_info',{
    params:{
      stroe_id:id,
      role_id:role_id.role_id
    },
    headers:{
      'access-token':token.value||''
    }
  })
  if (res_info.status == 200){
    if (res_info.data.current){
      console.log('角色信息:', res_info.data.data);
      formData.value.role_name = res_info.data.data.name
      formData.value.role = res_info.data.data.role
      formData.value.execute_code = res_info.data.data.authority
    }
  }
}

onMounted(async ()=>{
  await fetchRoleCodeList()
  await fetchRoleInfo()
})

// 监听role_id变化，重新获取数据
watch(() => role_id.role_id, async (newRoleId) => {
  if (newRoleId) {
    console.log('角色ID变化，重新获取数据:', newRoleId);
    await fetchRoleInfo()
  }
})

const rules = reactive({
  role_name: [{ required: true, message: '请输入权限名称', trigger: 'blur' },
                { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  role: [{ required: true, message: '请输入权限标识', trigger: 'blur' },
                { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' },
                { pattern: /^[a-zA-Z_][a-zA-Z0-9_]*$/, message: '权限标识只能包含字母、数字和下划线，且不能以数字开头', trigger: 'blur' }
  ],
  execute_code: [{ required: true, message: '请选择操作组合', trigger: 'change' },
                { type: 'array', min: 1, message: '至少选择一个操作组合', trigger: 'change' }
  ],
})

// 关闭弹窗
function close_dialog(){
  emit('childEvent', false)

}

async function commit_form(){
  if (!ruleFormRef.value) {
    console.error('表单引用未找到')
    return
  }
  ruleFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
        const patch_formdata = new FormData()
        const vul = sum(formData.value.execute_code || [])
        console.log(vul);
        patch_formdata.append('token',token.value||'')
        console.log(patch_formdata);
        patch_formdata.append('stroe_id',id.toString())
        patch_formdata.append('role_id',role_id.role_id.toString())
        patch_formdata.append('role_name',formData.value.role_name)
        patch_formdata.append('role',formData.value.role)
        patch_formdata.append('role_authority',vul.toString())
        const res = await Axios.patch('/buyer_update_role',patch_formdata)
        if (res.status == 200){
          if (res.data.current){
            ElMessage.success('更新成功')
            emit('childEvent', true)
          }else{
            ElMessage.error(res.data.message)
          }
        }
    }
  })
}


</script>
