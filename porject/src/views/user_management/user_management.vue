<template>
  <el-container>
    <el-header class="um-header">
      <ManagementNavigation />
    </el-header>
    <el-container class="um-body">
      <el-aside width="252px" class="um-aside">
        <UserManagmentNavigation @menu-selected="handleMenuSelect" />
      </el-aside>
      <el-main class="um-main">
        <div class="um-card">
          <component :is="mods" />
        </div>
      </el-main>
    </el-container>
    <el-footer class="footer-content">版权所有 © [xb商城]，保留所有权利。</el-footer>
  </el-container>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import ManagementNavigation from '@/moon/management_navigation.vue';
import UserManagmentNavigation from './content/user_managment_navigation.vue';
import MallApplyManagement from './content/mall_apply_management.vue';
import BusinessManagement from './content/business_management.vue';
import MallUsersManagement from './content/mall_users_management.vue';
import PlatformAdminUsers from './content/platform_admin_users.vue';
import RolePermissionManagement from './content/role_permission_management.vue';
import { hasAdminPermission } from '@/utils/adminPermission';

const mods = ref('MallApplyManagement');

function pickInitial() {
  if (hasAdminPermission('admin.user.merchant')) {
    mods.value = 'MallApplyManagement';
  } else if (hasAdminPermission('admin.user.mall')) {
    mods.value = 'MallUsersManagement';
  } else if (hasAdminPermission('admin.user.platform')) {
    mods.value = 'PlatformAdminUsers';
  } else if (hasAdminPermission('admin.user.role')) {
    mods.value = 'RolePermissionManagement';
  } else {
    mods.value = 'MallApplyManagement';
  }
}

onMounted(() => pickInitial());

defineOptions({
  name: 'UserManagement',
  components: {
    ManagementNavigation,
    UserManagmentNavigation,
    MallApplyManagement,
    BusinessManagement,
    MallUsersManagement,
    PlatformAdminUsers,
    RolePermissionManagement,
  },
});

const handleMenuSelect = (data: string) => {
  if (data === '1-1') mods.value = 'MallApplyManagement';
  else if (data === '1-2') mods.value = 'BusinessManagement';
  else if (data === '2') mods.value = 'MallUsersManagement';
  else if (data === '3') mods.value = 'PlatformAdminUsers';
  else if (data === '4') mods.value = 'RolePermissionManagement';
};
</script>

<style scoped>
.um-header {
  padding: 0 20px;
  height: auto;
  min-height: 60px;
}
.um-body {
  flex: 1;
}
.um-aside {
  padding: 12px 8px 20px;
  border-right: 1px solid var(--el-border-color-lighter);
}
.um-main {
  padding: 12px 16px 16px;
  flex: 1;
}
.um-card {
  width: 100%;
}
.footer-content {
  text-align: center;
  color: darkgray;
}
</style>
