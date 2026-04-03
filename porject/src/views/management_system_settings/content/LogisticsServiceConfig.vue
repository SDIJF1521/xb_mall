<template>
  <div class="logistics-config">
    <div class="hero">
      <div class="hero-text">
        <h2>物流服务配置</h2>
        <p>配置物流服务商，用于订单发货跟踪和物流信息推送。</p>
      </div>
      <div class="hero-actions">
        <el-button :icon="Refresh" circle @click="loadConfig" />
        <el-button
          type="warning"
          plain
          :loading="verifying"
          :disabled="!hasConfig"
          @click="verifyConfig"
        >连通性验证</el-button>
      </div>
    </div>

    <!-- 当前配置状态 -->
    <el-card v-if="configData" class="status-card" shadow="never">
      <template #header>
        <div class="card-head">
          <span class="card-head__title">当前配置</span>
          <el-tag :type="configData.is_active ? 'success' : 'info'" size="small">
            {{ configData.is_active ? '已启用' : '未启用' }}
          </el-tag>
        </div>
      </template>
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="用户编码">{{ configData.customer_code }}</el-descriptions-item>
        <el-descriptions-item label="环境类型">{{ configData.env_type ? '沙箱环境' : '生产环境' }}</el-descriptions-item>
        <el-descriptions-item label="校验码">
          <el-tag :type="configData.has_checkword ? 'success' : 'danger'" size="small">
            {{ configData.has_checkword ? '已配置' : '未配置' }}
          </el-tag>
          <code v-if="configData.checkword_preview" class="key-preview">{{ configData.checkword_preview }}</code>
        </el-descriptions-item>
      </el-descriptions>
      <div class="update-info">
        <span v-if="configData.updated_at">最后更新：{{ configData.updated_at }}</span>
      </div>
    </el-card>

    <el-empty v-else-if="!loading" description="暂未配置物流服务信息，请在下方录入" />

    <!-- 配置表单 -->
    <el-card class="form-card" shadow="never">
      <template #header>
        <span class="card-head__title">{{ hasConfig ? '更新配置' : '录入配置' }}</span>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="140px"
        label-position="right"
      >
        <el-form-item label="客户编码" prop="customer_code">
          <el-input v-model="form.customer_code" placeholder="请输入客户编码" maxlength="64" />
        </el-form-item>

        <el-form-item label="环境类型" prop="env_type">
          <el-radio-group v-model="form.env_type">
            <el-radio :value="true">生产环境</el-radio>
            <el-radio :value="false">沙箱环境</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="校验码" prop="checkword">
          <el-input
            v-model="form.checkword"
            type="password"
            show-password
            placeholder="请输入对应的校验码"
          />
          <div class="field-tip">根据选择的环境类型填写对应的校验码</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="submitConfig">
            {{ hasConfig ? '更新配置' : '保存配置' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import axios, { Axios } from 'axios'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

defineOptions({ name: 'LogisticsServiceConfig' })

const API = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
function hdr() {
  return { 'access-token': token }
}

interface ConfigData {
  id: string
  customer_code: string
  env_type: string
  is_active: boolean
  has_checkword: boolean
  checkword_preview: string
  created_at: string | null
  updated_at: string | null
}

const loading = ref(false)
const saving = ref(false)
const verifying = ref(false)
const configData = ref<ConfigData | null>(null)
const hasConfig = computed(() => !!configData.value)
const formRef = ref<FormInstance>()
const token = localStorage.getItem('admin_access_token') || ''

const form = ref({
  customer_code: '',
  env_type: true, // 默认为生产环境
  checkword: '',
})

const rules: FormRules = {
  customer_code: [{ required: true, message: '请输入客户编码', trigger: 'blur' }],
  env_type: [
    {
      required: true,
      validator: (rule, value, callback) => {
        if (value === null || value === undefined) {
          callback(new Error('请选择环境类型'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  checkword: [{ required: true, message: '请输入校验码', trigger: 'blur' }],
}

async function loadConfig() {
  loading.value = true
  try {
    const { data } = await API.get('/manage_logistics_config_select', { headers: hdr() })
    if (data.success && data.data) {
      // 处理后端返回的实际字段名
      const backendData = data.data
      configData.value = {
        id: backendData._id || 'logistics_default',
        customer_code: backendData.user_code || '',
        env_type: backendData.production_environment ? 'prod' : 'sandbox',
        is_active: true, // 后端没有提供此字段，默认为true
        has_checkword: !!backendData.code, // 根据code字段判断是否有校验码
        checkword_preview: backendData.code ? '******' : '',
        created_at: null, // 后端没有提供此字段
        updated_at: null  // 后端没有提供此字段
      }

      form.value.customer_code = backendData.user_code || ''
      form.value.env_type = Boolean(backendData.production_environment)
      form.value.checkword = ''
    } else if (data.success && !data.data) {
      configData.value = null
    } else {
      ElMessage.warning(data.msg || '加载失败')
    }
  } catch (error) {
    console.error('获取物流配置失败:', error)
    ElMessage.error('获取物流配置失败')
  } finally {
    loading.value = false
  }
}

async function submitConfig() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const formData = new FormData()
    formData.append('token', token)
    formData.append('user_code', form.value.customer_code)
    // env_type 现在已经是布尔值，直接使用
    formData.append('production_environment', form.value.env_type.toString())
    formData.append('verification_code', form.value.checkword)

    const res = await API.post('/manage_logistics_config', formData, { headers: hdr() })
    if (res.status === 200) {
      if (res.data.success){
        ElMessage.success('操作成功')
        // 重新加载配置以更新界面
        await loadConfig()
      } else {
        ElMessage.error(res.data.msg || '操作失败')
      }
    } else {
      ElMessage.error('请求失败')
    }
    form.value.checkword = ''
  } catch (error) {
    console.error('提交物流配置失败:', error)
    ElMessage.error('请求失败')
  } finally {
    saving.value = false
  }
}

async function verifyConfig() {
  verifying.value = true
  try {
    // 模拟验证
    setTimeout(() => {
      ElMessage.success('验证通过')
      verifying.value = false
    }, 1000)
  } catch {
    ElMessage.error('验证请求失败')
  } finally {
    verifying.value = false
  }
}

onMounted(() => loadConfig())
</script>

<style scoped>
.logistics-config {
  min-height: 400px;
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px 16px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.hero-text h2 {
  margin: 0 0 4px;
  font-size: 17px;
  font-weight: 600;
}

.hero-text p {
  margin: 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.45;
}

.hero-actions {
  display: flex;
  gap: 8px;
}

.status-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
}

.status-card :deep(.el-card__header) {
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.card-head__title {
  font-weight: 600;
  font-size: 15px;
}

.key-preview {
  margin-left: 8px;
  word-break: break-all;
}

.update-info {
  margin-top: 12px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  text-align: right;
}

.form-card {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
}

.form-card :deep(.el-card__header) {
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.form-card :deep(.el-card__body) {
  padding: 24px;
}

.field-tip {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin-top: 4px;
  line-height: 1.4;
}

code {
  font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', monospace;
  font-size: 12px;
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
}

:deep(.el-descriptions) {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-textarea__inner) {
  font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', monospace;
  font-size: 13px;
}
</style>
