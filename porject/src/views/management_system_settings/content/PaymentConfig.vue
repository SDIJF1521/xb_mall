<template>
  <div class="pay-config">
    <div class="hero">
      <div class="hero-text">
        <h2>支付配置</h2>
        <p>平台公共安全账户，配置支付宝公钥模式所需的 APPID、密钥和回调地址。</p>
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
        <el-descriptions-item label="APPID">{{ configData.app_id }}</el-descriptions-item>
        <el-descriptions-item label="签名类型">{{ configData.sign_type }}</el-descriptions-item>
        <el-descriptions-item label="网关地址" :span="2">{{ configData.server_url }}</el-descriptions-item>
        <el-descriptions-item label="异步通知地址" :span="2">{{ configData.notify_url || '未配置' }}</el-descriptions-item>
        <el-descriptions-item label="同步回调地址" :span="2">{{ configData.return_url || '未配置' }}</el-descriptions-item>
        <el-descriptions-item label="应用私钥">
          <el-tag :type="configData.has_private_key ? 'success' : 'danger'" size="small">
            {{ configData.has_private_key ? '已配置' : '未配置' }}
          </el-tag>
          <code v-if="configData.private_key_preview" class="key-preview">{{ configData.private_key_preview }}</code>
        </el-descriptions-item>
        <el-descriptions-item label="支付宝公钥">
          <el-tag :type="configData.has_public_key ? 'success' : 'danger'" size="small">
            {{ configData.has_public_key ? '已配置' : '未配置' }}
          </el-tag>
          <code v-if="configData.public_key_preview" class="key-preview">{{ configData.public_key_preview }}</code>
        </el-descriptions-item>
      </el-descriptions>
      <div class="update-info">
        <span v-if="configData.updated_at">最后更新：{{ configData.updated_at }}</span>
      </div>
    </el-card>

    <el-empty v-else-if="!loading" description="暂未配置支付信息，请在下方录入" />

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
        <el-form-item label="支付宝 APPID" prop="app_id">
          <el-input v-model="form.app_id" placeholder="请输入支付宝开放平台 APPID" maxlength="64" />
        </el-form-item>

        <el-form-item label="网关地址" prop="server_url">
          <el-select v-model="form.server_url" style="width: 100%;">
            <el-option label="正式环境" value="https://openapi.alipay.com/gateway.do" />
            <el-option label="沙箱环境" value="https://openapi-sandbox.dl.alipaydev.com/gateway.do" />
          </el-select>
        </el-form-item>

        <el-form-item label="签名类型">
          <el-radio-group v-model="form.sign_type">
            <el-radio value="RSA2">RSA2（推荐）</el-radio>
            <el-radio value="RSA">RSA</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="异步通知地址">
          <el-input v-model="form.notify_url" placeholder="https://yourdomain.com/api/pay/notify" />
        </el-form-item>

        <el-form-item label="同步回调地址">
          <el-input v-model="form.return_url" placeholder="https://yourdomain.com/pay/result" />
        </el-form-item>

        <el-divider content-position="left">密钥配置</el-divider>

        <el-form-item label="应用私钥" prop="app_private_key">
          <el-input
            v-model="form.app_private_key"
            type="textarea"
            :rows="4"
            placeholder="粘贴应用私钥（纯 Base64 字符串或完整 PEM 格式均可）"
            show-word-limit
          />
          <div class="field-tip">在支付宝开放平台「开发设置」→「接口加签方式」中获取</div>
        </el-form-item>

        <el-form-item label="支付宝公钥" prop="alipay_public_key">
          <el-input
            v-model="form.alipay_public_key"
            type="textarea"
            :rows="4"
            placeholder="粘贴支付宝公钥（纯 Base64 字符串或完整 PEM 格式均可）"
            show-word-limit
          />
          <div class="field-tip">在支付宝开放平台「开发设置」→「接口加签方式」→「支付宝公钥」中复制</div>
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
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

defineOptions({ name: 'PaymentConfig' })

const API = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
function hdr() {
  return { 'access-token': localStorage.getItem('admin_access_token') || '' }
}

interface ConfigData {
  id: string
  app_id: string
  server_url: string
  sign_type: string
  notify_url: string
  return_url: string
  is_active: boolean
  has_private_key: boolean
  has_public_key: boolean
  private_key_preview: string
  public_key_preview: string
  created_at: string | null
  updated_at: string | null
}

const loading = ref(false)
const saving = ref(false)
const verifying = ref(false)
const configData = ref<ConfigData | null>(null)
const hasConfig = computed(() => !!configData.value)
const formRef = ref<FormInstance>()

const form = ref({
  app_id: '',
  server_url: 'https://openapi.alipay.com/gateway.do',
  sign_type: 'RSA2',
  notify_url: '',
  return_url: '',
  app_private_key: '',
  alipay_public_key: '',
})

const rules: FormRules = {
  app_id: [{ required: true, message: '请输入 APPID', trigger: 'blur' }],
  server_url: [{ required: true, message: '请选择网关地址', trigger: 'change' }],
  app_private_key: [{ required: true, message: '请输入应用私钥', trigger: 'blur' }],
  alipay_public_key: [{ required: true, message: '请输入支付宝公钥', trigger: 'blur' }],
}

async function loadConfig() {
  loading.value = true
  try {
    const { data } = await API.get('/manage_pay_confing', { headers: hdr() })
    if (data.current && data.data) {
      configData.value = data.data
      form.value.app_id = data.data.app_id || ''
      form.value.server_url = data.data.server_url || 'https://openapi.alipay.com/gateway.do'
      form.value.sign_type = data.data.sign_type || 'RSA2'
      form.value.notify_url = data.data.notify_url || ''
      form.value.return_url = data.data.return_url || ''
      form.value.app_private_key = ''
      form.value.alipay_public_key = ''
    } else if (data.current && !data.data) {
      configData.value = null
    } else {
      ElMessage.warning(data.msg || '加载失败')
    }
  } catch {
    ElMessage.error('获取支付配置失败')
  } finally {
    loading.value = false
  }
}

async function submitConfig() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const { data } = await API.post('/manage_pay_confing', {
      app_id: form.value.app_id,
      server_url: form.value.server_url,
      sign_type: form.value.sign_type,
      notify_url: form.value.notify_url,
      return_url: form.value.return_url,
      app_private_key: form.value.app_private_key,
      alipay_public_key: form.value.alipay_public_key,
    }, { headers: hdr() })

    if (data.current) {
      ElMessage.success(data.msg || '保存成功')
      form.value.app_private_key = ''
      form.value.alipay_public_key = ''
      await loadConfig()
    } else {
      ElMessage.error(data.msg || '保存失败')
    }
  } catch {
    ElMessage.error('请求失败')
  } finally {
    saving.value = false
  }
}

async function verifyConfig() {
  verifying.value = true
  try {
    const { data } = await API.post('/manage_pay_confing/verify', null, { headers: hdr() })
    if (data.current && data.valid) {
      ElMessage.success(data.msg || '验证通过')
    } else if (data.current && !data.valid) {
      ElMessage.warning({ message: data.msg || '验证未通过', duration: 5000 })
    } else {
      ElMessage.error(data.msg || '验证失败')
    }
  } catch {
    ElMessage.error('验证请求失败')
  } finally {
    verifying.value = false
  }
}

onMounted(() => loadConfig())
</script>

<style scoped>
.pay-config {
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
