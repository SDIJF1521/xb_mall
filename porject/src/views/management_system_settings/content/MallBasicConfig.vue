<template>
  <div class="basic-config">
    <div class="hero">
      <div class="hero-text">
        <h2>基础配置</h2>
        <p>配置平台名称、简介、联系方式等基本信息。</p>
      </div>
      <div class="hero-actions">
        <el-button :icon="Refresh" circle @click="loadConfig" />
      </div>
    </div>

    <!-- 当前配置 -->
    <el-card v-if="configData" class="status-card" shadow="never">
      <template #header>
        <div class="card-head">
          <span class="card-head__title">当前配置</span>
          <el-tag type="success" size="small">已配置</el-tag>
        </div>
      </template>
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="平台名称">{{ configData.platform_name || '未设置' }}</el-descriptions-item>
        <el-descriptions-item label="联系邮箱">{{ configData.contact_email || '未设置' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ configData.contact_phone || '未设置' }}</el-descriptions-item>
        <el-descriptions-item label="ICP 备案号">{{ configData.icp_number || '未设置' }}</el-descriptions-item>
        <el-descriptions-item label="平台简介" :span="2">{{ configData.platform_desc || '未设置' }}</el-descriptions-item>
        <el-descriptions-item label="版权信息" :span="2">{{ configData.copyright_text || '未设置' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-empty v-else-if="!loading" description="暂未配置平台基础信息，请在下方录入" />

    <!-- 表单 -->
    <el-card class="form-card" shadow="never">
      <template #header>
        <span class="card-head__title">{{ configData ? '更新配置' : '录入配置' }}</span>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" label-position="right">
        <el-form-item label="平台名称" prop="platform_name">
          <el-input v-model="form.platform_name" placeholder="例如 xb商城" maxlength="64" show-word-limit />
        </el-form-item>

        <el-form-item label="平台简介" prop="platform_desc">
          <el-input v-model="form.platform_desc" type="textarea" :rows="3" placeholder="平台的简要介绍" maxlength="500" show-word-limit />
        </el-form-item>

        <el-form-item label="联系邮箱" prop="contact_email">
          <el-input v-model="form.contact_email" placeholder="例如 admin@example.com" maxlength="128" />
        </el-form-item>

        <el-form-item label="联系电话" prop="contact_phone">
          <el-input v-model="form.contact_phone" placeholder="例如 400-xxx-xxxx" maxlength="32" />
        </el-form-item>

        <el-form-item label="ICP 备案号" prop="icp_number">
          <el-input v-model="form.icp_number" placeholder="例如 京ICP备xxxxxxxx号" maxlength="64" />
        </el-form-item>

        <el-form-item label="版权信息" prop="copyright_text">
          <el-input v-model="form.copyright_text" placeholder="例如 版权所有 © 2025 xb商城" maxlength="256" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="submitConfig">
            {{ configData ? '更新配置' : '保存配置' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { updatePlatformCache } from '@/utils/platformConfig'

defineOptions({ name: 'MallBasicConfig' })

const API = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const token = localStorage.getItem('admin_access_token') || ''
function hdr() {
  return { 'access-token': token }
}

interface ConfigData {
  platform_name: string
  platform_desc: string
  contact_email: string
  contact_phone: string
  icp_number: string
  copyright_text: string
}

const loading = ref(false)
const saving = ref(false)
const configData = ref<ConfigData | null>(null)
const formRef = ref<FormInstance>()

const form = ref({
  platform_name: '',
  platform_desc: '',
  contact_email: '',
  contact_phone: '',
  icp_number: '',
  copyright_text: '',
})

const rules: FormRules = {
  platform_name: [{ required: true, message: '请输入平台名称', trigger: 'blur' }],
}

async function loadConfig() {
  loading.value = true
  try {
    const { data } = await API.get('/manage_platform_config_select', { headers: hdr() })
    if (data.success && data.data) {
      const d = data.data
      configData.value = { ...d }
      form.value.platform_name = d.platform_name || ''
      form.value.platform_desc = d.platform_desc || ''
      form.value.contact_email = d.contact_email || ''
      form.value.contact_phone = d.contact_phone || ''
      form.value.icp_number = d.icp_number || ''
      form.value.copyright_text = d.copyright_text || ''
    } else {
      configData.value = null
    }
  } catch (error) {
    console.error('获取基础配置失败:', error)
    ElMessage.error('获取基础配置失败')
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
    fd.append('platform_name', form.value.platform_name)
    fd.append('platform_desc', form.value.platform_desc)
    fd.append('contact_email', form.value.contact_email)
    fd.append('contact_phone', form.value.contact_phone)
    fd.append('icp_number', form.value.icp_number)
    fd.append('copyright_text', form.value.copyright_text)

    const res = await API.post('/manage_platform_config', fd, { headers: hdr() })
    if (res.data?.success) {
      ElMessage.success('操作成功')
      updatePlatformCache({
        platform_name: form.value.platform_name,
        copyright_text: form.value.copyright_text,
        icp_number: form.value.icp_number,
        contact_email: form.value.contact_email,
        contact_phone: form.value.contact_phone,
      })
      await loadConfig()
    } else {
      ElMessage.error(res.data?.msg || '操作失败')
    }
  } catch {
    ElMessage.error('请求失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => loadConfig())
</script>

<style scoped>
.basic-config {
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

:deep(.el-descriptions) {
  border-radius: 8px;
  overflow: hidden;
}
</style>
