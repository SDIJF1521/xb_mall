<template>
  <div class="plat-page">
    <div class="hero">
      <div>
        <h2>后台账号</h2>
        <p>管理平台登录账号、角色与密码；仅能操作您有权限管理的对象。</p>
      </div>
      <el-space>
        <el-button round :loading="loading" @click="load">刷新</el-button>
        <el-button v-if="canPlatform" type="primary" round @click="openAdd">新增账号</el-button>
      </el-space>
    </div>

    <el-card class="list-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="rows"
        stripe
        class="um-table"
        row-key="user"
        :header-cell-style="tableHeaderStyle"
        :row-style="{ height: '44px' }"
      >
        <template #empty>
          <el-empty description="暂无账号" />
        </template>
        <el-table-column label="账号" min-width="160">
          <template #default="{ row }">
            <span class="cell-user">
              <el-icon class="cell-user__icon"><User /></el-icon>
              <span class="uname">{{ row.user }}</span>
            </span>
          </template>
        </el-table-column>
        <el-table-column label="角色" min-width="140">
          <template #default="{ row }">
            <el-tag v-if="row.role_name" type="primary" effect="light" round>{{ row.role_name }}</el-tag>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column v-if="canPlatform" label="操作" width="260" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="openRole(row)">角色</el-button>
            <el-button size="small" link @click="openPwd(row.user)">改密</el-button>
            <el-button size="small" link type="danger" @click="remove(row.user)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="addVisible" title="新增后台账号" width="420px" destroy-on-close @closed="resetAdd">
      <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-position="top">
        <el-form-item label="用户名" prop="new_user">
          <el-input v-model="addForm.new_user" maxlength="20" show-word-limit autocomplete="off" />
        </el-form-item>
        <el-form-item label="密码" prop="new_password">
          <el-input
            v-model="addForm.new_password"
            type="password"
            show-password
            maxlength="20"
            show-word-limit
            autocomplete="new-password"
          />
        </el-form-item>
        <el-form-item label="角色" prop="role_id">
          <el-select v-model="addForm.role_id" filterable style="width: 100%">
            <el-option v-for="r in roleOptions" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addVisible = false">取消</el-button>
        <el-button type="primary" :loading="addLoading" @click="submitAdd">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="roleDlg" title="调整角色" width="400px" destroy-on-close>
      <p class="muted">账号：<strong>{{ roleTarget?.user }}</strong></p>
      <el-select v-model="rolePick" filterable style="width: 100%; margin-top: 12px">
        <el-option v-for="r in roleOptions" :key="r.id" :label="r.name" :value="r.id" />
      </el-select>
      <template #footer>
        <el-button @click="roleDlg = false">取消</el-button>
        <el-button type="primary" :loading="roleLoading" @click="submitRole">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="pwdVisible" title="修改密码" width="400px" destroy-on-close @closed="onPwdClosed">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-position="top">
        <el-form-item label="账号">
          <span>{{ pwdTarget }}</span>
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="pwdForm.new_password"
            type="password"
            show-password
            maxlength="20"
            show-word-limit
            autocomplete="new-password"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="pwdLoading" @click="submitPwd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import { hasAdminPermission } from '@/utils/adminPermission';
import { User } from '@element-plus/icons-vue';

defineOptions({ name: 'PlatformAdminUsers' });

const tableHeaderStyle = {
  background: 'var(--el-fill-color-light)',
  color: 'var(--el-text-color-regular)',
  fontWeight: '600',
};

/** 与 management_login 管理员登录一致 */
const addRules: FormRules = {
  new_user: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在3-20个字符', trigger: 'blur' },
  ],
  new_password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在6-20个字符', trigger: 'blur' },
  ],
  role_id: [{ required: true, message: '请选择角色', trigger: 'change' }],
};

const pwdRules: FormRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在6-20个字符', trigger: 'blur' },
  ],
};

const addFormRef = ref<FormInstance>();
const pwdFormRef = ref<FormInstance>();

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' });
function hdr() {
  const t = localStorage.getItem('admin_access_token');
  return { 'access-token': t || '' };
}

const canPlatform = computed(() => hasAdminPermission('admin.user.platform'));

const loading = ref(false);
const rows = ref<{ user: string; role_id: number | null; role_name: string }[]>([]);
const roleOptions = ref<{ id: number; name: string }[]>([]);

const addVisible = ref(false);
const addLoading = ref(false);
const addForm = reactive({ new_user: '', new_password: '', role_id: 1 });

const roleDlg = ref(false);
const roleLoading = ref(false);
const roleTarget = ref<{ user: string } | null>(null);
const rolePick = ref(1);

const pwdVisible = ref(false);
const pwdLoading = ref(false);
const pwdTarget = ref('');
const pwdForm = reactive({ new_password: '' });

function onPwdClosed() {
  pwdTarget.value = '';
  pwdForm.new_password = '';
  pwdFormRef.value?.clearValidate();
}

async function loadRoles() {
  try {
    const res = await Axios.get('/manage_role_list', { headers: hdr() });
    if (res.data.current) {
      roleOptions.value = (res.data.roles || []).map((r: { id: number; name: string }) => ({
        id: r.id,
        name: r.name,
      }));
    }
  } catch {
    /* ignore */
  }
}

async function load() {
  loading.value = true;
  try {
    const res = await Axios.get('/manage_platform_user_list', { headers: hdr() });
    if (res.data.current) {
      const raw = res.data.user_list || [];
      rows.value = raw.map((item: unknown) => {
        if (typeof item === 'string') {
          return { user: item, role_id: null, role_name: '' };
        }
        const o = item as Record<string, unknown>;
        return {
          user: String(o.user ?? ''),
          role_id: o.role_id != null && o.role_id !== '' ? Number(o.role_id) : null,
          role_name: o.role_name != null ? String(o.role_name) : '',
        };
      });
    } else {
      ElMessage.warning(res.data.msg || '加载失败');
      rows.value = [];
    }
    await loadRoles();
  } catch {
    ElMessage.error('请求失败');
  } finally {
    loading.value = false;
  }
}

function openAdd() {
  resetAdd();
  addVisible.value = true;
}
function resetAdd() {
  addForm.new_user = '';
  addForm.new_password = '';
  addForm.role_id = roleOptions.value[0]?.id ?? 1;
  addFormRef.value?.clearValidate();
}

async function submitAdd() {
  const af = addFormRef.value;
  if (!af) return;
  try {
    await af.validate();
  } catch {
    return;
  }
  addLoading.value = true;
  try {
    const res = await Axios.post(
      '/manage_platform_user_add',
      {
        new_user: addForm.new_user.trim(),
        new_password: addForm.new_password,
        role_id: addForm.role_id,
      },
      { headers: hdr() },
    );
    if (res.data.current) {
      ElMessage.success(res.data.msg);
      addVisible.value = false;
      await load();
    } else ElMessage.error(res.data.msg);
  } catch {
    ElMessage.error('请求失败');
  } finally {
    addLoading.value = false;
  }
}

function openPwd(user: string) {
  pwdTarget.value = user;
  pwdForm.new_password = '';
  pwdVisible.value = true;
}

async function submitPwd() {
  const pf = pwdFormRef.value;
  if (!pf) return;
  try {
    await pf.validate();
  } catch {
    return;
  }
  pwdLoading.value = true;
  try {
    const res = await Axios.post(
      '/manage_platform_user_password',
      { target_user: pwdTarget.value, new_password: pwdForm.new_password },
      { headers: hdr() },
    );
    if (res.data.current) {
      ElMessage.success(res.data.msg);
      pwdVisible.value = false;
    } else ElMessage.error(res.data.msg);
  } catch {
    ElMessage.error('请求失败');
  } finally {
    pwdLoading.value = false;
  }
}

function openRole(row: { user: string; role_id: number | null }) {
  roleTarget.value = row;
  rolePick.value = row.role_id ?? 1;
  roleDlg.value = true;
}

async function submitRole() {
  if (!roleTarget.value) return;
  roleLoading.value = true;
  try {
    const res = await Axios.post(
      '/manage_platform_user_role',
      { target_user: roleTarget.value.user, role_id: rolePick.value },
      { headers: hdr() },
    );
    if (res.data.current) {
      ElMessage.success(res.data.msg);
      roleDlg.value = false;
      await load();
    } else ElMessage.error(res.data.msg);
  } catch {
    ElMessage.error('请求失败');
  } finally {
    roleLoading.value = false;
  }
}

async function remove(user: string) {
  try {
    await ElMessageBox.confirm(`确定删除账号「${user}」？`, '确认', { type: 'warning' });
  } catch {
    return;
  }
  try {
    const res = await Axios.post('/manage_platform_user_delete', { target_user: user }, { headers: hdr() });
    if (res.data.current) {
      ElMessage.success(res.data.msg);
      await load();
    } else ElMessage.error(res.data.msg);
  } catch {
    ElMessage.error('请求失败');
  }
}

onMounted(() => load());
</script>

<style scoped>
.plat-page {
  width: 100%;
  max-width: 100%;
}
.list-card {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
  overflow: hidden;
}
.list-card :deep(.el-card__body) {
  padding: 0;
}
.um-table {
  width: 100%;
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
.uname {
  font-weight: 500;
}
.muted {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
</style>
