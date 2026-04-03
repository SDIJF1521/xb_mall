<template>
  <div class="email-config">
    <div class="hero">
      <div class="hero-text">
        <h2>邮件服务配置</h2>
        <p>配置 SMTP 邮件服务，用于发送验证码、通知等系统邮件。</p>
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
          <el-tag type="success" size="small">已配置</el-tag>
        </div>
      </template>
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="发件邮箱">{{ configData.sender_email }}</el-descriptions-item>
        <el-descriptions-item label="发件人名称">{{ configData.sender_name }}</el-descriptions-item>
        <el-descriptions-item label="SMTP 服务器">{{ configData.smtp_server }}</el-descriptions-item>
        <el-descriptions-item label="SMTP 端口">{{ configData.smtp_port }}</el-descriptions-item>
        <el-descriptions-item label="连接方式">
          <el-tag :type="configData.use_ssl ? 'success' : 'warning'" size="small">
            {{ configData.use_ssl ? 'SSL 加密' : 'STARTTLS' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="授权码">
          <el-tag :type="configData.has_password ? 'success' : 'danger'" size="small">
            {{ configData.has_password ? '已配置' : '未配置' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-empty v-else-if="!loading" description="暂未配置邮件服务，请在下方录入" />

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
        <el-form-item label="发件邮箱" prop="sender_email">
          <el-input v-model="form.sender_email" placeholder="例如 notify@example.com" maxlength="128" />
        </el-form-item>

        <el-form-item label="SMTP 授权码" prop="sender_password">
          <el-input
            v-model="form.sender_password"
            type="password"
            show-password
            placeholder="邮箱 SMTP 授权码（非登录密码）"
          />
          <div class="field-tip">QQ 邮箱 / 163 邮箱需在邮箱设置中开启 SMTP 并生成授权码</div>
        </el-form-item>

        <el-form-item label="SMTP 服务器" prop="smtp_server">
          <el-input v-model="form.smtp_server" placeholder="例如 smtp.qq.com" maxlength="128" />
        </el-form-item>

        <el-form-item label="SMTP 端口" prop="smtp_port">
          <el-input-number v-model="form.smtp_port" :min="1" :max="65535" :step="1" />
          <div class="field-tip">SSL 通常为 465，STARTTLS 通常为 587</div>
        </el-form-item>

        <el-form-item label="连接方式" prop="use_ssl">
          <el-radio-group v-model="form.use_ssl">
            <el-radio :value="true">SSL（推荐）</el-radio>
            <el-radio :value="false">STARTTLS</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="发件人名称" prop="sender_name">
          <el-input v-model="form.sender_name" placeholder="收件人看到的发件人名称" maxlength="64" />
          <div class="field-tip">默认"系统通知"，可修改为商城名称</div>
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

defineOptions({ name: 'EmailServiceConfig' })

const API = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const token = localStorage.getItem('admin_access_token') || ''
function hdr() {
  return { 'access-token': token }
}

interface ConfigData {
  sender_email: string
  smtp_server: string
  smtp_port: number
  use_ssl: boolean
  sender_name: string
  has_password: boolean
}

const loading = ref(false)
const saving = ref(false)
const verifying = ref(false)
const configData = ref<ConfigData | null>(null)
const hasConfig = computed(() => !!configData.value)
const formRef = ref<FormInstance>()

const form = ref({
  sender_email: '',
  sender_password: '',
  smtp_server: '',
  smtp_port: 465,
  use_ssl: true,
  sender_name: '系统通知',
})

const rules: FormRules = {
  sender_email: [
    { required: true, message: '请输入发件邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  sender_password: [{ required: true, message: '请输入 SMTP 授权码', trigger: 'blur' }],
  smtp_server: [{ required: true, message: '请输入 SMTP 服务器地址', trigger: 'blur' }],
  smtp_port: [{ required: true, message: '请输入端口', trigger: 'blur' }],
  sender_name: [{ required: true, message: '请输入发件人名称', trigger: 'blur' }],
}

async function loadConfig() {
  loading.value = true
  try {
    const { data } = await API.get('/manage_email_config_select', { headers: hdr() })
    if (data.success && data.data) {
      const d = data.data
      configData.value = {
        sender_email: d.sender_email || '',
        smtp_server: d.smtp_server || '',
        smtp_port: d.smtp_port || 465,
        use_ssl: d.use_ssl !== false,
        sender_name: d.sender_name || '系统通知',
        has_password: !!d.has_password,
      }
      form.value.sender_email = d.sender_email || ''
      form.value.smtp_server = d.smtp_server || ''
      form.value.smtp_port = d.smtp_port || 465
      form.value.use_ssl = d.use_ssl !== false
      form.value.sender_name = d.sender_name || '系统通知'
      form.value.sender_password = ''
    } else {
      configData.value = null
    }
  } catch (error) {
    console.error('获取邮件配置失败:', error)
    ElMessage.error('获取邮件配置失败')
  } finally {
    loading.value = false
  }
}

async function submitConfig() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const fd = new FormData()
    fd.append('token', token)
    fd.append('sender_email', form.value.sender_email)
    fd.append('sender_password', form.value.sender_password)
    fd.append('smtp_server', form.value.smtp_server)
    fd.append('smtp_port', String(form.value.smtp_port))
    fd.append('use_ssl', String(form.value.use_ssl))
    fd.append('sender_name', form.value.sender_name)

    const res = await API.post('/manage_email_config', fd, { headers: hdr() })
    if (res.data?.success) {
      ElMessage.success('操作成功')
      await loadConfig()
    } else {
      ElMessage.error(res.data?.msg || '操作失败')
    }
    form.value.sender_password = ''
  } catch (error) {
    console.error('提交邮件配置失败:', error)
    ElMessage.error('请求失败')
  } finally {
    saving.value = false
  }
}

async function verifyConfig() {
  verifying.value = true
  try {
    const fd = new FormData()
    fd.append('token', token)
    const res = await API.post('/manage_email_config/verify', fd, { headers: hdr() })
    if (res.data?.success) {
      ElMessage.success(res.data.msg || '连通性验证通过')
    } else {
      ElMessage.error(res.data.msg || '连通性验证失败')
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
.email-config {
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

:deep(.el-descriptions) {
  border-radius: 8px;
  overflow: hidden;
}
</style>
