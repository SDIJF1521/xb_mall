<template>
  <div class="mall-page">
    <div class="hero">
      <div>
        <h2>商城用户</h2>
        <p>C 端注册用户列表（仅用户名），数据来自全站用户表。</p>
      </div>
      <el-button type="primary" round :loading="loading" @click="load">刷新</el-button>
    </div>
    <el-card class="list-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="rows"
        stripe
        class="um-table"
        row-key="name"
        :header-cell-style="tableHeaderStyle"
        :row-style="{ height: '44px' }"
      >
        <template #empty>
          <el-empty description="暂无商城用户" />
        </template>
        <el-table-column type="index" label="#" width="64" align="center" />
        <el-table-column label="用户名" min-width="220">
          <template #default="{ row }">
            <span class="cell-user">
              <el-icon class="cell-user__icon"><User /></el-icon>
              {{ row.name }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { User } from '@element-plus/icons-vue';

defineOptions({ name: 'MallUsersManagement' });

const tableHeaderStyle = {
  background: 'var(--el-fill-color-light)',
  color: 'var(--el-text-color-regular)',
  fontWeight: '600',
};

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' });
const loading = ref(false);
const rows = ref<{ name: string }[]>([]);

async function load() {
  loading.value = true;
  try {
    const fd = new FormData();
    fd.append('token', localStorage.getItem('admin_access_token') || '');
    const res = await Axios.post('/user_list', fd);
    if (res.data.current && Array.isArray(res.data.user_list)) {
      rows.value = res.data.user_list.map((name: string) => ({ name }));
    } else {
      ElMessage.warning(res.data.msg || '加载失败');
      rows.value = [];
    }
  } catch {
    ElMessage.error('请求失败');
  } finally {
    loading.value = false;
  }
}

onMounted(() => load());
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
</style>
