<template>
  <div class="pay-config">
    <!-- 页头 -->
    <div class="hero">
      <div class="hero-left">
        <div class="hero-icon-wrap">
          <el-icon :size="22"><CreditCard /></el-icon>
        </div>
        <div>
          <h2>店铺支付配置</h2>
          <p>配置支付宝公钥模式所需的 APPID、密钥和回调地址，用于店铺独立收款。</p>
        </div>
      </div>
      <div class="hero-actions">
        <el-tooltip content="刷新配置" placement="top">
          <el-button :icon="Refresh" circle @click="loadConfig" :loading="loading" />
        </el-tooltip>
        <el-button
          type="warning"
          :loading="verifying"
          :disabled="!hasConfig"
          round
          @click="verifyConfig"
        >
          <el-icon style="margin-right:6px"><Connection /></el-icon>
          连通性验证
        </el-button>
      </div>
    </div>

    <!-- 验证结果横幅 -->
    <transition name="banner-slide">
      <el-alert
        v-if="verifyResult"
        :title="verifyResult.msg"
        :type="verifyResult.ok ? 'success' : 'error'"
        show-icon
        closable
        class="verify-banner"
        @close="verifyResult = null"
      />
    </transition>

    <!-- 店铺选择器（多店铺时显示） -->
    <el-card v-if="mallList.length > 1" class="section-card store-picker" shadow="never">
      <div class="store-picker__inner">
        <div class="store-picker__label">
          <el-icon :size="16"><Shop /></el-icon>
          <span>当前店铺</span>
        </div>
        <el-select
          v-model="currentMallId"
          placeholder="请选择店铺"
          @change="onMallChange"
          style="width: 260px;"
        >
          <el-option
            v-for="mall in mallList"
            :key="mall.id"
            :label="mall.name"
            :value="mall.id"
          />
        </el-select>
      </div>
    </el-card>

    <!-- 无店铺提示 -->
    <el-alert
      v-if="!currentMallId"
      title="未找到关联店铺，请先创建店铺"
      type="warning"
      show-icon
      :closable="false"
      class="no-store-alert"
    />

    <template v-if="currentMallId">
      <!-- 加载骨架屏 -->
      <el-card v-if="loading" class="section-card" shadow="never">
        <el-skeleton :rows="5" animated />
      </el-card>

      <template v-else>
        <!-- 当前配置概览 -->
        <el-card v-if="configData" class="section-card status-card" shadow="never">
          <template #header>
            <div class="card-head">
              <div class="card-head__left">
                <div class="card-head__dot" :class="configData.is_active ? 'is-on' : 'is-off'" />
                <span class="card-head__title">当前配置</span>
              </div>
              <el-tag
                :type="configData.is_active ? 'success' : 'info'"
                size="small"
                round
                effect="light"
              >
                {{ configData.is_active ? '已启用' : '未启用' }}
              </el-tag>
            </div>
          </template>

          <!-- 指标网格 -->
          <div class="metric-grid">
            <div class="metric-item">
              <span class="metric-label">APPID</span>
              <span class="metric-value mono">{{ configData.app_id }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">签名类型</span>
              <el-tag size="small" type="primary" effect="plain" round>{{ configData.sign_type }}</el-tag>
            </div>
            <div class="metric-item span-2">
              <span class="metric-label">网关地址</span>
              <span class="metric-value mono small">{{ configData.server_url }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">异步通知地址</span>
              <span class="metric-value mono small" :class="{ 'is-empty': !configData.notify_url }">
                {{ configData.notify_url || '未配置' }}
              </span>
            </div>
            <div class="metric-item">
              <span class="metric-label">同步回调地址</span>
              <span class="metric-value mono small" :class="{ 'is-empty': !configData.return_url }">
                {{ configData.return_url || '未配置' }}
              </span>
            </div>
          </div>

          <!-- 密钥状态 -->
          <div class="key-status-row">
            <div class="key-chip" :class="configData.has_private_key ? 'is-ok' : 'is-miss'">
              <el-icon :size="14"><Lock /></el-icon>
              <span>应用私钥</span>
              <el-tag :type="configData.has_private_key ? 'success' : 'danger'" size="small" round>
                {{ configData.has_private_key ? '已配置' : '未配置' }}
              </el-tag>
              <code v-if="configData.private_key_preview" class="key-preview">{{ configData.private_key_preview }}</code>
            </div>
            <div class="key-chip" :class="configData.has_public_key ? 'is-ok' : 'is-miss'">
              <el-icon :size="14"><Key /></el-icon>
              <span>支付宝公钥</span>
              <el-tag :type="configData.has_public_key ? 'success' : 'danger'" size="small" round>
                {{ configData.has_public_key ? '已配置' : '未配置' }}
              </el-tag>
              <code v-if="configData.public_key_preview" class="key-preview">{{ configData.public_key_preview }}</code>
            </div>
          </div>

          <div v-if="configData.updated_at" class="update-info">
            <el-icon :size="12"><Timer /></el-icon>
            最后更新：{{ configData.updated_at }}
          </div>
        </el-card>

        <!-- 空状态 -->
        <el-card v-else class="section-card empty-card" shadow="never">
          <el-empty description="暂未配置支付信息" :image-size="80">
            <template #description>
              <p class="empty-desc">暂未配置支付信息，请在下方录入支付宝公钥模式所需参数。</p>
            </template>
          </el-empty>
        </el-card>

        <!-- 配置表单 -->
        <el-card class="section-card form-card" shadow="never">
          <template #header>
            <div class="card-head">
              <div class="card-head__left">
                <el-icon :size="16" color="var(--el-color-primary)"><Edit /></el-icon>
                <span class="card-head__title">{{ hasConfig ? '更新配置' : '录入配置' }}</span>
              </div>
            </div>
          </template>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-width="140px"
            label-position="right"
            class="config-form"
          >
            <!-- 基础信息分组 -->
            <div class="form-section-title">
              <span class="form-section-dot" />
              基础信息
            </div>

            <el-form-item label="支付宝 APPID" prop="app_id">
              <el-input v-model="form.app_id" placeholder="请输入支付宝开放平台 APPID" maxlength="64" clearable>
                <template #prefix><el-icon><Tickets /></el-icon></template>
              </el-input>
            </el-form-item>

            <el-form-item label="网关地址" prop="server_url">
              <el-select v-model="form.server_url" style="width: 100%;" placeholder="请选择网关地址">
                <el-option label="正式环境  openapi.alipay.com" value="https://openapi.alipay.com/gateway.do" />
                <el-option label="沙箱环境  openapi-sandbox" value="https://openapi-sandbox.dl.alipaydev.com/gateway.do" />
              </el-select>
            </el-form-item>

            <el-form-item label="签名类型">
              <el-radio-group v-model="form.sign_type">
                <el-radio-button value="RSA2">RSA2（推荐）</el-radio-button>
                <el-radio-button value="RSA">RSA</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <!-- 回调地址分组 -->
            <div class="form-section-title">
              <span class="form-section-dot" />
              回调地址
            </div>

            <el-form-item label="异步通知地址">
              <el-input v-model="form.notify_url" placeholder="https://yourdomain.com/api/pay/notify" clearable>
                <template #prefix><el-icon><Link /></el-icon></template>
              </el-input>
            </el-form-item>

            <el-form-item label="同步回调地址">
              <el-input v-model="form.return_url" placeholder="https://yourdomain.com/pay/result" clearable>
                <template #prefix><el-icon><Link /></el-icon></template>
              </el-input>
            </el-form-item>

            <!-- 密钥分组 -->
            <div class="form-section-title">
              <span class="form-section-dot is-key" />
              密钥配置
            </div>

            <el-form-item label="应用私钥" prop="app_private_key">
              <el-input
                v-model="form.app_private_key"
                type="textarea"
                :rows="4"
                placeholder="粘贴应用私钥（纯 Base64 字符串或完整 PEM 格式均可）"
                resize="vertical"
              />
              <div class="field-tip">
                <el-icon :size="12"><InfoFilled /></el-icon>
                在支付宝开放平台「开发设置」→「接口加签方式」中获取
              </div>
            </el-form-item>

            <el-form-item label="支付宝公钥" prop="alipay_public_key">
              <el-input
                v-model="form.alipay_public_key"
                type="textarea"
                :rows="4"
                placeholder="粘贴支付宝公钥（纯 Base64 字符串或完整 PEM 格式均可）"
                resize="vertical"
              />
              <div class="field-tip">
                <el-icon :size="12"><InfoFilled /></el-icon>
                在支付宝开放平台「开发设置」→「接口加签方式」→「支付宝公钥」中复制
              </div>
            </el-form-item>

            <el-form-item class="submit-row">
              <el-button
                type="primary"
                :loading="saving"
                round
                size="large"
                class="submit-btn"
                @click="submitConfig"
              >
                <el-icon style="margin-right:6px"><Check /></el-icon>
                {{ hasConfig ? '更新配置' : '保存配置' }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import {
  Refresh, CreditCard, Connection, Shop, Lock, Key, Timer,
  Edit, Tickets, Link, InfoFilled, Check,
} from '@element-plus/icons-vue'

defineOptions({ name: 'BuyerPayConfig' })

const API = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
function hdr() {
  return { 'Access-Token': localStorage.getItem('buyer_access_token') || '' }
}

function parseToken(): { station: string; mall_id?: number; state_id_list?: number[]; user?: string } | null {
  const token = localStorage.getItem('buyer_access_token')
  if (!token) return null
  try {
    const b64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(b64))
  } catch {
    return null
  }
}

interface MallItem { id: number; name: string }

interface ConfigData {
  id: string
  mall_id: number
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
const verifyResult = ref<{ ok: boolean; msg: string } | null>(null)

const mallList = ref<MallItem[]>([])
const currentMallId = ref<number | null>(null)

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

async function initMallList() {
  const payload = parseToken()
  if (!payload) return

  if (payload.station === '2' && payload.mall_id) {
    mallList.value = [{ id: payload.mall_id, name: `店铺 ${payload.mall_id}` }]
    currentMallId.value = payload.mall_id
  } else if (payload.station === '1' && payload.state_id_list?.length) {
    mallList.value = payload.state_id_list.map(id => ({ id, name: `店铺 ${id}` }))
    currentMallId.value = payload.state_id_list[0]
  }

  if (currentMallId.value) {
    await loadMallNames()
    await loadConfig()
  }
}

async function loadMallNames() {
  try {
    const token = localStorage.getItem('buyer_access_token') || ''
    for (const mall of mallList.value) {
      const { data } = await API.post('/buyer_get_mall_info', { token, id: mall.id })
      if (data.current && data.data?.mall_name) {
        mall.name = data.data.mall_name
      }
    }
  } catch {
    // 获取名称失败时保留默认名称
  }
}

function onMallChange() {
  configData.value = null
  verifyResult.value = null
  resetForm()
  loadConfig()
}

function resetForm() {
  form.value = {
    app_id: '',
    server_url: 'https://openapi.alipay.com/gateway.do',
    sign_type: 'RSA2',
    notify_url: '',
    return_url: '',
    app_private_key: '',
    alipay_public_key: '',
  }
}

async function loadConfig() {
  if (!currentMallId.value) return
  loading.value = true
  try {
    const { data } = await API.get('/buyer_pay_config', {
      headers: hdr(),
      params: { stroe_id: currentMallId.value },
    })
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
    const { data } = await API.post('/buyer_pay_config', {
      stroe_id: currentMallId.value,
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
  if (!currentMallId.value) return
  verifying.value = true
  verifyResult.value = null
  try {
    const { data } = await API.post('/buyer_pay_config/verify', null, {
      headers: hdr(),
      params: { stroe_id: currentMallId.value },
    })
    if (data.current && data.valid) {
      verifyResult.value = { ok: true, msg: data.msg || '验证通过' }
    } else if (data.current && !data.valid) {
      verifyResult.value = { ok: false, msg: data.msg || '验证未通过' }
    } else {
      verifyResult.value = { ok: false, msg: data.msg || '验证失败' }
    }
  } catch {
    verifyResult.value = { ok: false, msg: '验证请求失败，请检查网络' }
  } finally {
    verifying.value = false
  }
}

onMounted(() => initMallList())
</script>

<style scoped lang="scss">
.pay-config {
  min-height: 400px;
}

/* ── 页头 hero ── */
.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.hero-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.hero-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--el-color-primary-light-8), var(--el-color-primary-light-5));
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.hero-left h2 {
  margin: 0 0 2px;
  font-size: 17px;
  font-weight: 700;
}

.hero-left p {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* ── 验证结果横幅 ── */
.verify-banner {
  margin-bottom: 16px;
  border-radius: 10px;
}

.banner-slide-enter-active,
.banner-slide-leave-active {
  transition: all 0.3s ease;
}

.banner-slide-enter-from,
.banner-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ── 通用 section-card ── */
.section-card {
  margin-bottom: 18px;
  border-radius: 14px;
  border: 1px solid var(--el-border-color-lighter);
  transition: box-shadow 0.3s;

  &:hover {
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05);
  }

  :deep(.el-card__header) {
    padding: 14px 20px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }

  :deep(.el-card__body) {
    padding: 20px;
  }
}

/* ── 店铺选择器 ── */
.store-picker__inner {
  display: flex;
  align-items: center;
  gap: 16px;
}

.store-picker__label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
  color: var(--el-text-color-primary);
}

.no-store-alert {
  margin-bottom: 16px;
  border-radius: 10px;
}

/* ── 卡片头部 ── */
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-head__left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-head__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;

  &.is-on {
    background: var(--el-color-success);
    box-shadow: 0 0 6px var(--el-color-success);
    animation: dot-pulse 2s infinite;
  }

  &.is-off {
    background: var(--el-color-info-light-5);
  }
}

@keyframes dot-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.card-head__title {
  font-weight: 700;
  font-size: 15px;
}

/* ── 指标网格 ── */
.metric-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  overflow: hidden;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  border-right: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
  transition: background 0.2s;

  &:hover {
    background: var(--el-fill-color-light);
  }

  &:nth-child(even) {
    border-right: none;
  }

  &:nth-last-child(-n+2) {
    border-bottom: none;
  }

  &.span-2 {
    grid-column: span 2;
    border-right: none;
  }
}

.metric-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
}

.metric-value {
  font-size: 14px;
  color: var(--el-text-color-primary);
  font-weight: 600;
  word-break: break-all;

  &.mono {
    font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', monospace;
  }

  &.small {
    font-size: 13px;
    font-weight: 500;
  }

  &.is-empty {
    color: var(--el-text-color-placeholder);
    font-weight: 400;
  }
}

/* ── 密钥状态 ── */
.key-status-row {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.key-chip {
  flex: 1;
  min-width: 240px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  transition: transform 0.2s;

  &.is-ok {
    background: var(--el-color-success-light-9);
    border: 1px solid var(--el-color-success-light-7);
    color: var(--el-color-success-dark-2);
  }

  &.is-miss {
    background: var(--el-color-danger-light-9);
    border: 1px solid var(--el-color-danger-light-7);
    color: var(--el-color-danger-dark-2);
  }
}

.key-preview {
  margin-left: auto;
  font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', monospace;
  font-size: 11px;
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 8px;
  border-radius: 4px;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── 更新时间 ── */
.update-info {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 14px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  justify-content: flex-end;
}

/* ── 空状态 ── */
.empty-card :deep(.el-card__body) {
  padding: 32px 20px;
}

.empty-desc {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

/* ── 表单卡片 ── */
.form-card :deep(.el-card__body) {
  padding: 24px 28px;
}

.config-form {
  max-width: 680px;
}

.form-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 20px 0 16px;
  padding-left: 2px;

  &:first-child {
    margin-top: 0;
  }
}

.form-section-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--el-color-primary);
  flex-shrink: 0;

  &.is-key {
    background: var(--el-color-warning);
  }
}

.field-tip {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin-top: 6px;
  line-height: 1.4;
}

.submit-row {
  margin-top: 8px;
}

.submit-btn {
  min-width: 180px;
  font-weight: 600;
  letter-spacing: 0.5px;
  transition: transform 0.15s;

  &:active {
    transform: scale(0.97);
  }
}

/* ── 表单内全局细调 ── */
:deep(.el-textarea__inner) {
  font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', monospace;
  font-size: 13px;
  border-radius: 8px;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-select) .el-input__wrapper {
  border-radius: 8px;
}

:deep(.el-radio-button__inner) {
  border-radius: 8px !important;
}

:deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 8px 0 0 8px !important;
}

:deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 8px 8px 0 !important;
}
</style>
