<template>
  <div class="side-nav">
    <div class="side-title">用户中心</div>
    <el-menu
      :default-active="defaultActive"
      class="nav-menu"
      @select="handleSelect"
    >
      <el-sub-menu v-if="showMerchant" index="1">
        <template #title>
          <el-icon><IconBuildingStore /></el-icon>
          <span>商家管理</span>
        </template>
        <el-menu-item v-if="hasPerm('admin.user.merchant')" index="1-1">商家申请合验</el-menu-item>
        <el-menu-item v-if="hasPerm('admin.user.merchant')" index="1-2">商家账号管理</el-menu-item>
      </el-sub-menu>

      <el-menu-item v-if="hasPerm('admin.user.mall')" index="2">
        <el-icon><IconUsers /></el-icon>
        <span>商城用户管理</span>
      </el-menu-item>

      <el-menu-item v-if="hasPerm('admin.user.platform')" index="3">
        <el-icon><IconUser /></el-icon>
        <span>后台账号</span>
      </el-menu-item>

      <el-menu-item v-if="hasPerm('admin.user.role')" index="4">
        <el-icon><IconShield /></el-icon>
        <span>角色与权限</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { IconBuildingStore, IconUsers, IconUser, IconShield } from '@tabler/icons-vue';
import { computed } from 'vue';
import { hasAdminPermission } from '@/utils/adminPermission';

defineOptions({
  name: 'UserManagmentNavigation',
  components: {
    IconBuildingStore,
    IconUsers,
    IconUser,
    IconShield,
  },
});

const emit = defineEmits(['menu-selected']);

const showMerchant = computed(
  () => hasAdminPermission('admin.user.merchant'),
);

const defaultActive = computed(() => {
  if (hasAdminPermission('admin.user.merchant')) return '1-1';
  if (hasAdminPermission('admin.user.mall')) return '2';
  if (hasAdminPermission('admin.user.platform')) return '3';
  if (hasAdminPermission('admin.user.role')) return '4';
  return '1-1';
});

function hasPerm(code: string) {
  return hasAdminPermission(code);
}

function handleSelect(index: string) {
  emit('menu-selected', index);
}
</script>

<style scoped>
.side-nav {
  padding: 8px 6px;
}
.side-title {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--el-text-color-secondary);
  padding: 4px 10px 8px;
}
.nav-menu {
  border-right: none;
  background: transparent;
}
.nav-menu :deep(.el-menu-item),
.nav-menu :deep(.el-sub-menu__title) {
  border-radius: 10px;
  margin-bottom: 4px;
}
.nav-menu :deep(.el-menu-item.is-active) {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 600;
}
.dark .nav-menu :deep(.el-menu-item.is-active) {
  background-color: #409eff;
  color: #fff;
}
</style>
