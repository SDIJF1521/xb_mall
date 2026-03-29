<template>
  <el-container>
    <ManagementNavigation />
    <el-container>
      <el-aside width="220px" class="promo-aside">
        <el-menu :default-active="activeTab" class="promo-menu" @select="handleTabSelect">
          <el-menu-item index="coupon">
            <el-icon><Ticket /></el-icon>
            <span>优惠券管理</span>
          </el-menu-item>
          <el-menu-item index="activity">
            <el-icon><Lightning /></el-icon>
            <span>促销活动</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main class="promo-main">
        <component :is="currentView" />
      </el-main>
    </el-container>
    <el-footer class="footer-content">版权所有 © [xb商城]，保留所有权利。</el-footer>
  </el-container>
</template>

<script setup lang="ts">
import { shallowRef, type Component } from 'vue'
import ManagementNavigation from '@/moon/management_navigation.vue'
import { Ticket, Lightning } from '@element-plus/icons-vue'
import CouponManagement from '@/views/management_system_settings/content/CouponManagement.vue'
import ActivityManagement from '@/views/management_system_settings/content/ActivityManagement.vue'

defineOptions({ name: 'ManagementPromotion' })

const activeTab = shallowRef('coupon')
const currentView = shallowRef<Component>(CouponManagement)

function handleTabSelect(index: string) {
  activeTab.value = index
  currentView.value = index === 'activity' ? ActivityManagement : CouponManagement
}
</script>

<style scoped>
.footer-content {
  text-align: center;
  color: darkgray;
}
.promo-aside {
  height: calc(100vh - 120px);
  padding: 20px 10px;
  border-right: 1px solid var(--el-border-color);
}
.promo-menu {
  border-right: none;
  background: transparent;
}
.promo-menu :deep(.el-menu-item) {
  height: 48px;
  line-height: 48px;
  margin-bottom: 8px;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
}
.promo-menu :deep(.el-menu-item.is-active) {
  background-color: var(--el-color-primary);
  color: white;
  font-weight: 600;
}
.promo-menu :deep(.el-menu-item:not(.is-active):hover) {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  transform: translateX(4px);
}
.promo-main {
  padding: 20px;
}
</style>
