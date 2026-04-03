<template>
<el-container>
    <ManagementNavigation/>
    <el-container>
      <el-aside width="250px" class="system-settings-aside">
        <el-menu
          :default-active="activeIndex"
          :default-openeds="defaultOpeneds"
          class="system-settings-menu"
          @select="handleMenuSelect"
        >
          <!-- 商城设置 -->
          <el-sub-menu index="1">
            <template #title>
              <el-icon><Shop /></el-icon>
              <span>商城设置</span>
            </template>
            <el-menu-item index="1-1">基础配置</el-menu-item>
            <el-menu-item index="1-2">支付配置</el-menu-item>
            <el-menu-item index="1-3">物流配置</el-menu-item>
          </el-sub-menu>

          <!-- 活动设置 -->
          <el-sub-menu index="2">
            <template #title>
              <el-icon><Lightning /></el-icon>
              <span>活动设置</span>
            </template>
            <el-menu-item index="2-1">优惠券管理</el-menu-item>
            <el-menu-item index="2-2">促销活动</el-menu-item>
            <el-menu-item index="2-3">秒杀活动</el-menu-item>
            <el-menu-item index="2-4">满减活动</el-menu-item>
          </el-sub-menu>

          <!-- 广告设置 -->
          <el-menu-item index="3">
            <el-icon><Picture /></el-icon>
            <template #title>广告设置</template>
          </el-menu-item>

          <!-- 系统设置 -->
          <el-sub-menu index="4">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统设置</span>
            </template>
            <el-menu-item index="4-1">系统参数</el-menu-item>
            <el-menu-item index="4-2">邮件配置</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>

      <el-main class="system-settings-main">
        <div class="settings-content">
          <component :is="currentView" />
        </div>
      </el-main>
    </el-container>

  <el-footer class="footer-content">{{ platformInfo.copyright_text }}<template v-if="platformInfo.icp_number"> | {{ platformInfo.icp_number }}</template></el-footer>
</el-container>
</template>

<script setup lang="ts">
import { ref, computed, shallowRef, onMounted, type Component } from 'vue'
import ManagementNavigation from '@/moon/management_navigation.vue'
import { usePlatformConfig } from '@/utils/platformConfig'
import {
  Shop,
  Lightning,
  Picture,
  Setting,
} from '@element-plus/icons-vue'

import AdSetting from './content/AdSetting.vue'
import PaymentConfig from './content/PaymentConfig.vue'
import CouponManagement from './content/CouponManagement.vue'
import ActivityManagement from './content/ActivityManagement.vue'
import LogisticsServiceConfig from './content/LogisticsServiceConfig.vue'
import EmailServiceConfig from './content/EmailServiceConfig.vue'
import MallBasicConfig from './content/MallBasicConfig.vue'
import SystemParameters from './content/SystemParameters.vue'

const MallMemberLevel = { template: '<div><h3>会员等级</h3><p>这里是会员等级配置内容</p></div>' }
const PermissionManagement = { template: '<div><h3>权限管理</h3><p>这里是权限管理内容</p></div>' }

defineOptions({
  name: 'ManagementSystemSettings',
})

const { platformInfo } = usePlatformConfig()

const STORAGE_KEY = 'admin_settings_active_menu'

const activeIndex = ref(sessionStorage.getItem(STORAGE_KEY) || '1-1')
const currentView = shallowRef<Component>(MallBasicConfig)

const defaultOpeneds = computed(() => {
  const idx = activeIndex.value
  if (idx.includes('-')) return [idx.split('-')[0]]
  return []
})

const viewMap: Record<string, Component> = {
  '1-1': MallBasicConfig,
  '1-2': PaymentConfig,
  '1-3': LogisticsServiceConfig,
  '1-4': MallMemberLevel,
  '2-1': CouponManagement,
  '2-2': ActivityManagement,
  '2-3': ActivityManagement,
  '2-4': ActivityManagement,
  '3': AdSetting,
  '4-1': SystemParameters,
  '4-2': EmailServiceConfig,
  '5': PermissionManagement,
}

function applyView(index: string) {
  currentView.value = viewMap[index] || MallBasicConfig
}

function handleMenuSelect(index: string) {
  activeIndex.value = index
  sessionStorage.setItem(STORAGE_KEY, index)
  applyView(index)
}

onMounted(() => {
  applyView(activeIndex.value)
})
</script>

<style lang="scss" scoped>
.footer-content {
  text-align: center;
  color: darkgray;
}

.system-settings-aside {
  height: calc(100vh - 120px);
  padding: 20px 10px;
  border-right: 1px solid var(--el-border-color);
}

.system-settings-menu {
  border-right: none;
  background: transparent;

  :deep(.el-menu-item),
  :deep(.el-sub-menu__title) {
    height: 48px;
    line-height: 48px;
    margin-bottom: 8px;
    border-radius: 8px;
    font-size: 14px;
    transition: all 0.3s ease;
    position: relative;

    &.is-active {
      background-color: var(--el-color-primary);
      color: white;
      font-weight: 600;

      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 24px;
        background-color: white;
        border-radius: 2px;
      }
    }

    &:not(.is-active):hover {
      background-color: var(--el-color-primary-light-9);
      color: var(--el-color-primary);
      transform: translateX(4px);
    }
  }

  :deep(.el-sub-menu) {
    .el-menu {
      :deep(.el-menu-item) {
        height: 42px;
        line-height: 42px;
        padding-left: 40px !important;

        &.is-active {
          background-color: var(--el-color-primary-light-9);
          color: var(--el-color-primary);

          &::before {
            display: none;
          }
        }
      }
    }
  }

  :deep(.el-icon) {
    margin-right: 8px;
    font-size: 16px;
  }
}

.system-settings-main {
  padding: 20px;
}

.settings-content {
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 20px;
  min-height: calc(100vh - 200px);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
</style>
