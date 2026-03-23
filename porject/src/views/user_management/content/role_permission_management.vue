<template>
  <div class="role-page">
    <div class="hero">
      <div class="hero-text">
        <h2>角色与权限</h2>
        <p>为角色勾选能力；也可在下方输入任意自定义权限码（每行一个），保存后生效。</p>
      </div>
      <el-button type="primary" round :loading="loading" @click="loadAll">刷新</el-button>
    </div>

    <el-card class="list-card" shadow="never">
      <template #header>
        <div class="card-head">
          <span class="card-head__title">角色列表</span>
          <el-button type="success" plain size="small" @click="openEdit(null)">＋ 新建角色</el-button>
        </div>
      </template>
      <el-table
        v-loading="loading"
        :data="roles"
        stripe
        class="um-table role-table"
        row-key="id"
        :header-cell-style="tableHeaderStyle"
        :row-style="{ height: '44px' }"
      >
        <template #empty>
          <el-empty description="暂无角色" />
        </template>
        <el-table-column prop="id" label="ID" width="72" align="center" />
        <el-table-column label="角色名" min-width="140">
          <template #default="{ row }">
            <span class="cell-role">
              <el-icon><Key /></el-icon>
              {{ row.name }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="180" show-overflow-tooltip />
        <el-table-column label="权限数" width="96" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" round>{{ row.permissions?.length ?? 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button
              v-if="row.id !== 1"
              type="danger"
              link
              @click="removeRole(row)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dlg"
      :title="editId ? '编辑角色' : '新建角色'"
      width="min(640px, 96vw)"
      destroy-on-close
      class="role-dlg"
      @closed="resetDlg"
    >
      <el-form label-position="top">
        <el-form-item label="角色名称">
          <el-input v-model="form.name" maxlength="64" show-word-limit />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" maxlength="255" />
        </el-form-item>
        <el-form-item label="超级权限">
          <el-checkbox :model-value="form.permissions.includes('*')" @change="toggleStar">
            全部权限（*）
          </el-checkbox>
        </el-form-item>
        <el-form-item v-show="!form.permissions.includes('*')" label="预定义权限">
          <el-collapse>
            <el-collapse-item
              v-for="cat in categories"
              :key="cat"
              :title="cat"
              :name="cat"
            >
              <el-checkbox-group v-model="form.permissions">
                <el-checkbox
                  v-for="item in byCat[cat]"
                  :key="item.code"
                  :label="item.code"
                  border
                  class="perm-cb"
                >
                  {{ item.name }}
                  <span class="code">{{ item.code }}</span>
                </el-checkbox>
              </el-checkbox-group>
            </el-collapse-item>
          </el-collapse>
        </el-form-item>
        <el-form-item v-show="!form.permissions.includes('*')" label="自定义权限码（每行一个，可随意命名）">
          <el-input
            v-model="customCodes"
            type="textarea"
            :rows="4"
            placeholder="例如：report.export&#10;partner.api"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Key } from '@element-plus/icons-vue';

defineOptions({ name: 'RolePermissionManagement' });

const tableHeaderStyle = {
  background: 'var(--el-fill-color-light)',
  color: 'var(--el-text-color-regular)',
  fontWeight: '600',
};

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' });
function hdr() {
  const t = localStorage.getItem('admin_access_token');
  return { 'access-token': t || '' };
}

interface CatItem {
  code: string;
  name: string;
  category: string;
}
interface RoleRow {
  id: number;
  name: string;
  description: string;
  permissions: string[];
}

const loading = ref(false);
const saving = ref(false);
const catalog = ref<CatItem[]>([]);
const roles = ref<RoleRow[]>([]);
const dlg = ref(false);
const editId = ref<number | null>(null);
const form = ref({ name: '', description: '', permissions: [] as string[] });
const customCodes = ref('');

const categories = computed(() => {
  const s = new Set<string>();
  catalog.value.forEach((c) => s.add(c.category || '其他'));
  return [...s];
});

const byCat = computed(() => {
  const m: Record<string, CatItem[]> = {};
  catalog.value.forEach((c) => {
    const k = c.category || '其他';
    if (!m[k]) m[k] = [];
    m[k].push(c);
  });
  return m;
});

async function loadAll() {
  loading.value = true;
  try {
    const [c, r] = await Promise.all([
      Axios.get('/manage_permission_catalog', { headers: hdr() }),
      Axios.get('/manage_role_list', { headers: hdr() }),
    ]);
    if (c.data.current) catalog.value = c.data.catalog || [];
    if (r.data.current) roles.value = r.data.roles || [];
    if (!c.data.current) ElMessage.warning(c.data.msg || '权限目录加载失败');
    if (!r.data.current) ElMessage.warning(r.data.msg || '角色列表加载失败');
  } catch {
    ElMessage.error('请求失败');
  } finally {
    loading.value = false;
  }
}

function toggleStar(v: boolean | string | number) {
  form.value.permissions = v ? ['*'] : [];
}

function openEdit(row: RoleRow | null) {
  if (row) {
    editId.value = row.id;
    form.value = {
      name: row.name,
      description: row.description || '',
      permissions: [...(row.permissions || [])],
    };
    const preset = new Set(catalog.value.map((x) => x.code));
    const extra = (row.permissions || []).filter((p) => !preset.has(p) && p !== '*');
    customCodes.value = extra.join('\n');
    if (row.permissions?.includes('*')) {
      form.value.permissions = ['*'];
    }
  } else {
    editId.value = null;
    form.value = { name: '', description: '', permissions: [] };
    customCodes.value = '';
  }
  dlg.value = true;
}

function resetDlg() {
  editId.value = null;
  form.value = { name: '', description: '', permissions: [] };
  customCodes.value = '';
}

async function save() {
  const name = form.value.name.trim();
  if (!name) {
    ElMessage.warning('请填写角色名');
    return;
  }
  let perms = [...form.value.permissions];
  if (perms.includes('*')) {
    perms = ['*'];
  } else {
    const lines = customCodes.value
      .split(/\r?\n/)
      .map((s) => s.trim())
      .filter(Boolean);
    perms = [...new Set([...perms, ...lines])];
  }
  saving.value = true;
  try {
    const res = await Axios.post(
      '/manage_role_save',
      { id: editId.value ?? 0, name, description: form.value.description, permissions: perms },
      { headers: hdr() },
    );
    if (res.data.current) {
      ElMessage.success(res.data.msg);
      dlg.value = false;
      await loadAll();
    } else ElMessage.error(res.data.msg);
  } catch {
    ElMessage.error('保存失败');
  } finally {
    saving.value = false;
  }
}

async function removeRole(row: RoleRow) {
  try {
    await ElMessageBox.confirm(`删除角色「${row.name}」？`, '确认', { type: 'warning' });
  } catch {
    return;
  }
  try {
    const res = await Axios.post('/manage_role_delete', { role_id: row.id }, { headers: hdr() });
    if (res.data.current) {
      ElMessage.success(res.data.msg);
      await loadAll();
    } else ElMessage.error(res.data.msg);
  } catch {
    ElMessage.error('删除失败');
  }
}

onMounted(() => loadAll());
</script>

<style scoped>
.role-page {
  width: 100%;
  max-width: 100%;
}
.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px 16px;
  margin-bottom: 12px;
  padding-bottom: 10px;
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
.list-card {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
  overflow: hidden;
}
.list-card :deep(.el-card__header) {
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.list-card :deep(.el-card__body) {
  padding: 0;
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
.um-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}
.cell-role {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.cell-role .el-icon {
  color: var(--el-color-warning);
  font-size: 16px;
}
.perm-cb {
  margin: 4px 8px 4px 0;
  display: inline-flex;
  align-items: center;
}
.code {
  margin-left: 6px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-family: ui-monospace, monospace;
}
:deep(.role-dlg .el-collapse-item__header) {
  font-weight: 500;
}
</style>
