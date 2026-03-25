<template>
<el-container>
    <ManagementNavigation/>
    <el-container>
      <el-aside width="250px" class="system-settings-aside">
        <el-menu
          :default-active="activeIndex"
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
            <el-menu-item index="1-4">会员等级</el-menu-item>
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
            <el-menu-item index="4-3">短信配置</el-menu-item>
            <el-menu-item index="4-4">安全设置</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>

      <el-main class="system-settings-main">
        <div class="settings-content">
          <component :is="currentView" />
        </div>
      </el-main>
    </el-container>

  <el-footer class="footer-content">版权所有 © [xb商城]，保留所有权利。</el-footer>
</el-container>
</template>

<script setup lang="ts">
import { ref, shallowRef } from 'vue'
import ManagementNavigation from '@/moon/management_navigation.vue'
import {
  Shop,
  Lightning,
  Picture,
  Setting,
  Key
} from '@element-plus/icons-vue'

// 导入可能的子组件（占位用，实际开发时需要创建对应的组件）
const MallBasicConfig = { template: '<div><h3>商城基础配置</h3><p>这里是商城的基础配置内容</p></div>' }
const MallPaymentConfig = { template: '<div><h3>支付配置</h3><p>这里是支付配置内容</p></div>' }
const MallLogisticsConfig = { template: '<div><h3>物流配置</h3><p>这里是物流配置内容</p></div>' }
const MallMemberLevel = { template: '<div><h3>会员等级</h3><p>这里是会员等级配置内容</p></div>' }
const CouponManagement = { template: '<div><h3>优惠券管理</h3><p>这里是优惠券管理内容</p></div>' }
const PromotionActivity = { template: '<div><h3>促销活动</h3><p>这里是促销活动配置内容</p></div>' }
const FlashSaleActivity = { template: '<div><h3>秒杀活动</h3><p>这里是秒杀活动配置内容</p></div>' }
const FullReductionActivity = { template: '<div><h3>满减活动</h3><p>这里是满减活动配置内容</p></div>' }
const AdSetting = { template: '<div><h3>广告设置</h3><p>这里是广告设置内容</p></div>' }
const SystemParameters = { template: '<div><h3>系统参数</h3><p>这里是系统参数配置内容</p></div>' }
const EmailConfig = { template: '<div><h3>邮件配置</h3><p>这里是邮件配置内容</p></div>' }
const SmsConfig = { template: '<div><h3>短信配置</h3><p>这里是短信配置内容</p></div>' }
const SecuritySetting = { template: '<div><h3>安全设置</h3><p>这里是安全设置内容</p></div>' }
const PermissionManagement = { template: '<div><h3>权限管理</h3><p>这里是权限管理内容</p></div>' }

defineOptions({
  name: 'ManagementSystemSettings',
})

const activeIndex = ref('1-1')
const currentView = shallowRef(MallBasicConfig)

function handleMenuSelect(index: string) {
  activeIndex.value = index

  // 根据选中的菜单项切换对应的内容组件
  switch(index) {
    // 商城设置相关
    case '1-1':
      currentView.value = MallBasicConfig
      break
    case '1-2':
      currentView.value = MallPaymentConfig
      break
    case '1-3':
      currentView.value = MallLogisticsConfig
      break
    case '1-4':
      currentView.value = MallMemberLevel
      break
    // 活动设置相关
    case '2-1':
      currentView.value = CouponManagement
      break
    case '2-2':
      currentView.value = PromotionActivity
      break
    case '2-3':
      currentView.value = FlashSaleActivity
      break
    case '2-4':
      currentView.value = FullReductionActivity
      break
    // 广告设置
    case '3':
      currentView.value = AdSetting
      break
    // 系统设置相关
    case '4-1':
      currentView.value = SystemParameters
      break
    case '4-2':
      currentView.value = EmailConfig
      break
    case '4-3':
      currentView.value = SmsConfig
      break
    case '4-4':
      currentView.value = SecuritySetting
      break
    // 权限管理
    case '5':
      currentView.value = PermissionManagement
      break
    default:
      currentView.value = MallBasicConfig
  }
}
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
