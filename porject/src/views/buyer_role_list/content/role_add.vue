<template>
    <el-form
    ref="ruleFormRef"
    label-width="auto"
    :model="formData"
    :rules="rules"
    @submit.prevent="submitForm"
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
      <el-button size="small" type="primary" style="width: 100%;" @click="submitForm">提交</el-button>
    </el-col>
    <el-col :span="12">
      <el-button size="small" type="danger" style="width: 100%;" @click="closeDialog">取消</el-button>
    </el-col>
  </el-row>
</template>
<script lang="ts" setup>
import axios from 'axios'
import { useRoute } from 'vue-router'
import {ref,onMounted,reactive} from 'vue'
import { ElMessage } from 'element-plus'
import { sum } from 'element-plus/es/components/table-v2/src/utils.mjs'

// 定义事件
const emit = defineEmits(['child-event'])

defineOptions({
  name: 'RoleAdd'
})

// 定义axios实例
const Axioos = axios.create({
  baseURL: "http://127.0.0.1:8000/api"
});

const token = ref(localStorage.getItem('buyer_access_token')||'')
const route = useRoute().params
const mall_id = ref(route.id)
const ruleFormRef = ref() // 修正：在setup中定义ref
interface FormData {
  role_name: string
  role:string
  execute_code?: number[]

}

const role_code_list = ref([])

const formData = ref<FormData>({
  role_name: '',
  role:'',
  execute_code: undefined
})

onMounted(async ()=>{
  const formdata = new FormData()
  formdata.append('token',token.value)
  const res = await Axioos.post('/buyer_role_code_get',formdata)
  if (res.status == 200){
    if (res.data.current){
      console.log(res.data.data);
      role_code_list.value = res.data.data
    }
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

// 关闭对话框
const closeDialog = () => {
  // 重置表单
  resetForm()
  // 向父组件发送关闭事件
  emit('child-event', false)
}

// 重置表单
const resetForm = () => {
  if (ruleFormRef.value) {
    ruleFormRef.value.resetFields()
  }
  formData.value.execute_code = []
}
// 提交表单
const submitForm = async () => {
  if (!ruleFormRef.value) {
    console.error('表单引用未找到')
    return
  }

  ruleFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
        const add_formdata = new FormData()
        const vul = sum(formData.value.execute_code || [])
        console.log(vul);
        add_formdata.append('token',token.value)
        console.log(add_formdata);
        add_formdata.append('stroe_id',mall_id.value.toString())
        add_formdata.append('role_name',formData.value.role_name)
        add_formdata.append('role',formData.value.role)
        add_formdata.append('role_authority',vul.toString())
        const res = await Axioos.post('/buyer_role_add',add_formdata)
        if (res.status == 200){
          if (res.data.current){
            ElMessage.success('添加成功')
            closeDialog()
          }
        }



    }

  })
}

</script>
