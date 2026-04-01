<template>
  <div class="mall-page">
    <div class="hero">
      <div>
        <h2>商城用户</h2>
        <p>管理 C 端注册用户：查看、搜索、冻结 / 解冻、重置密码。</p>
      </div>
      <el-button type="primary" round :loading="loading" @click="load">刷新</el-button>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" @submit.prevent="load">
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="用户名 / 邮箱"
            clearable
            style="width: 200px"
            @clear="load"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 120px" @change="load">
            <el-option label="正常" :value="0" />
            <el-option label="已冻结" :value="1" />
          </el-select>
        </el-form-item>
        <el-form-item label="身份">
          <el-select v-model="filters.merchant" placeholder="全部" clearable style="width: 120px" @change="load">
            <el-option label="买家" :value="0" />
            <el-option label="卖家" :value="1" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户列表 -->
    <el-card class="list-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="rows"
        stripe
        class="um-table"
        row-key="username"
        :header-cell-style="tableHeaderStyle"
        :row-style="{ height: '48px' }"
      >
        <template #empty>
          <el-empty description="暂无商城用户" />
        </template>
        <el-table-column type="index" label="#" width="56" align="center" />
        <el-table-column label="用户名" min-width="150">
          <template #default="{ row }">
            <span class="cell-user">
              <el-icon class="cell-user__icon"><User /></el-icon>
              {{ row.username }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="邮箱" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.email || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="身份" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.merchant === 1" type="warning" effect="light" round size="small">卖家</el-tag>
            <el-tag v-else effect="light" round size="small">买家</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" width="130" align="center">
          <template #default="{ row }">
            <span class="muted">{{ row.register_time || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 1" type="danger" effect="dark" round size="small">已冻结</el-tag>
            <el-tag v-else type="success" effect="light" round size="small">正常</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 0"
              size="small"
              link
              type="warning"
              @click="confirmFreeze(row, 'freeze')"
            >冻结</el-button>
            <el-button
              v-else
              size="small"
              link
              type="success"
              @click="confirmFreeze(row, 'unfreeze')"
            >解冻</el-button>
            <el-button size="small" link type="primary" @click="openResetPwd(row)">重置密码</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 15, 30, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="load"
          @current-change="load"
        />
      </div>
    </el-card>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="resetPwdVisible" title="重置用户密码" width="440px" destroy-on-close @closed="resetPwdForm.new_password = ''">
      <el-form ref="resetPwdFormRef" :model="resetPwdForm" :rules="resetPwdRules" label-position="top">
        <el-form-item label="用户">
          <el-input :model-value="resetPwdForm.username" disabled />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="resetPwdForm.new_password"
            type="password"
            show-password
            maxlength="40"
            placeholder="至少8位，包含字母和数字"
            autocomplete="new-password"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="resetPwdLoading" @click="submitResetPwd">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { User } from '@element-plus/icons-vue'

defineOptions({ name: 'MallUsersManagement' })

const tableHeaderStyle = {
  background: 'var(--el-fill-color-light)',
  color: 'var(--el-text-color-regular)',
  fontWeight: '600',
}

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

interface MallUser {
  username: string
  email: string
  merchant: number
  register_time: string | null
  status: number
}

const loading = ref(false)
const rows = ref<MallUser[]>([])
const page = ref(1)
const pageSize = ref(15)
const total = ref(0)

const filters = reactive({
  keyword: '',
  status: undefined as number | undefined,
  merchant: undefined as number | undefined,
})

function resetFilters() {
  filters.keyword = ''
  filters.status = undefined
  filters.merchant = undefined
  page.value = 1
  load()
}

async function load() {
  loading.value = true
  try {
    const token = localStorage.getItem('admin_access_token') || ''
    const params: Record<string, any> = {
      token,
      page: page.value,
      page_size: pageSize.value,
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.status !== undefined && filters.status !== null) params.status = filters.status
    if (filters.merchant !== undefined && filters.merchant !== null) params.merchant = filters.merchant

    const res = await Axios.get('/manage_mall_user_list', { params })
    if (res.data.current) {
      rows.value = res.data.user_list || []
      total.value = res.data.total || 0
    } else {
      ElMessage.warning(res.data.msg || '加载失败')
      rows.value = []
      total.value = 0
    }
  } catch {
    ElMessage.error('请求失败')
  } finally {
    loading.value = false
  }
}

// ── 冻结 / 解冻 ──
async function confirmFreeze(row: MallUser, action: 'freeze' | 'unfreeze') {
  const label = action === 'freeze' ? '冻结' : '解冻'
  try {
    await ElMessageBox.confirm(
      `确定要${label}用户「${row.username}」吗？${action === 'freeze' ? '冻结后该用户将无法登录。' : ''}`,
      `${label}确认`,
      { confirmButtonText: '确定', cancelButtonText: '取消', type: action === 'freeze' ? 'warning' : 'info' }
    )
  } catch {
    return
  }
  try {
    const fd = new FormData()
    fd.append('token', localStorage.getItem('admin_access_token') || '')
    fd.append('username', row.username)
    fd.append('action', action)
    const res = await Axios.post('/manage_mall_user_freeze', fd)
    if (res.data.current) {
      ElMessage.success(res.data.msg || `${label}成功`)
      await load()
    } else {
      ElMessage.warning(res.data.msg || `${label}失败`)
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

// ── 重置密码 ──
const resetPwdVisible = ref(false)
const resetPwdLoading = ref(false)
const resetPwdFormRef = ref<FormInstance>()
const resetPwdForm = reactive({ username: '', new_password: '' })

const validatePassword = (_rule: any, value: string, callback: any) => {
  if (!value) return callback(new Error('请输入新密码'))
  if (value.length < 8) return callback(new Error('密码至少8位'))
  const hasDigit = /\d/.test(value)
  const hasLetter = /[a-zA-Z]/.test(value)
  if (!hasDigit || !hasLetter) return callback(new Error('密码必须包含字母和数字'))
  callback()
}
const resetPwdRules: FormRules = {
  new_password: [{ required: true, validator: validatePassword, trigger: 'blur' }],
}

function openResetPwd(row: MallUser) {
  resetPwdForm.username = row.username
  resetPwdForm.new_password = ''
  resetPwdVisible.value = true
}

async function submitResetPwd() {
  if (!resetPwdFormRef.value) return
  const valid = await resetPwdFormRef.value.validate().catch(() => false)
  if (!valid) return
  resetPwdLoading.value = true
  try {
    const fd = new FormData()
    fd.append('token', localStorage.getItem('admin_access_token') || '')
    fd.append('username', resetPwdForm.username)
    fd.append('new_password', resetPwdForm.new_password)
    const res = await Axios.post('/manage_mall_user_reset_password', fd)
    if (res.data.current) {
      ElMessage.success(res.data.msg || '密码重置成功')
      resetPwdVisible.value = false
    } else {
      ElMessage.warning(res.data.msg || '重置失败')
    }
  } catch {
    ElMessage.error('请求失败')
  } finally {
    resetPwdLoading.value = false
  }
}

onMounted(() => load())
</script>

<style scoped>
.mall-page {
  width: 100%;
  max-width: 100%;
}
.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px 16px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.hero h2 {
  margin: 0 0 4px;
  font-size: 17px;
  font-weight: 600;
}
.hero p {
  margin: 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.45;
}
.filter-card {
  margin-bottom: 12px;
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
}
.filter-card :deep(.el-card__body) {
  padding: 16px 20px 4px;
}
.filter-card :deep(.el-form-item) {
  margin-bottom: 12px;
}
.list-card {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
  overflow: hidden;
}
.list-card :deep(.el-card__body) {
  padding: 0;
}
.um-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}
.cell-user {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.cell-user__icon {
  font-size: 18px;
  color: var(--el-color-primary);
}
.muted {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: 14px 20px;
}
</style>
