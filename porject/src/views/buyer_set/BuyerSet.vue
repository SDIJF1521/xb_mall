<template>
  <el-container>
    <el-container>
      <BuyerNavigation />
      <el-container>
        <el-header>
          <BuyerHead />
        </el-header>
        <el-main class="system-main">
          <el-container class="system-container">
            <el-aside width="240px" class="system-aside">
              <div class="aside-header">
                <el-icon class="aside-header__icon"><Operation /></el-icon>
                <span class="aside-header__text">系统管理</span>
              </div>
              <el-menu
                :default-active="activeIndex"
                class="system-menu"
                @select="handleMenuSelect"
              >
                <el-menu-item index="1">
                  <el-icon><Setting /></el-icon>
                  <span>基本设置</span>
                </el-menu-item>
                <el-menu-item index="2">
                  <el-icon><CreditCard /></el-icon>
                  <span>支付配置</span>
                </el-menu-item>
              </el-menu>
            </el-aside>

            <el-main class="system-content">
              <transition name="view-fade" mode="out-in">
                <component :is="currentView" :key="activeIndex" />
              </transition>
            </el-main>
          </el-container>
        </el-main>
      </el-container>
    </el-container>
    <el-footer class="footer-content">版权所有 ©[xb商城]，保留所有权利。</el-footer>
  </el-container>
</template>

<script setup lang="ts">
import { ref, shallowRef, onMounted } from 'vue'
import { Setting, CreditCard, Operation } from '@element-plus/icons-vue'
import BuyerHead from '@/moon/buyer_head.vue'
import BuyerNavigation from '@/moon/buyer_navigation.vue'
import BuyerTheme from '@/moon/buyer_theme'
import SetList from '@/views/buyer_set/content/SetList.vue'
import BuyerPayConfig from '@/views/buyer_set/content/BuyerPayConfig.vue'

defineOptions({ name: 'BuyerSet' })

const activeIndex = ref('1')
const currentView = shallowRef(SetList)

function handleMenuSelect(index: string) {
  activeIndex.value = index
  switch (index) {
    case '1':
      currentView.value = SetList
      break
    case '2':
      currentView.value = BuyerPayConfig
      break
    default:
      currentView.value = SetList
  }
}

onMounted(() => {
  new BuyerTheme().initTheme()
})
</script>

<style lang="scss" scoped>
.footer-content {
  text-align: center;
  color: darkgray;
}

:deep(.el-header) {
  border-bottom: 1px solid var(--el-border-color-light);
  padding-bottom: 10px;
  margin-bottom: 10px;
}

.system-main {
  padding: 0;
}

.system-container {
  height: calc(100vh - 130px);
}

/* ── 侧栏 ── */
.system-aside {
  padding: 0;
  border-right: 1px solid var(--el-border-color-lighter);
  overflow-y: auto;
  background: var(--el-bg-color);
}

.aside-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 22px 20px 18px;
  border-bottom: 1px solid var(--el-border-color-lighter);

  &__icon {
    font-size: 20px;
    color: var(--el-color-primary);
  }

  &__text {
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: var(--el-text-color-primary);
  }
}

.system-menu {
  border-right: none;
  background: transparent;
  padding: 12px 10px;

  :deep(.el-menu-item) {
    height: 48px;
    line-height: 48px;
    margin-bottom: 4px;
    border-radius: 10px;
    font-size: 14px;
    color: var(--el-text-color-regular);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%) scaleY(0);
      width: 3px;
      height: 20px;
      border-radius: 0 3px 3px 0;
      background: var(--el-color-primary);
      transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    &.is-active {
      background: var(--el-color-primary-light-9);
      color: var(--el-color-primary);
      font-weight: 600;

      &::before {
        transform: translateY(-50%) scaleY(1);
      }

      .el-icon {
        color: var(--el-color-primary);
      }
    }

    &:not(.is-active):hover {
      background: var(--el-fill-color-light);
      color: var(--el-color-primary);
      padding-left: 24px;
    }
  }

  :deep(.el-icon) {
    margin-right: 10px;
    font-size: 17px;
    transition: color 0.25s;
  }
}

/* ── 内容区 ── */
.system-content {
  padding: 24px 28px;
  overflow-y: auto;
  background: var(--el-fill-color-blank);
}

/* ── 视图切换动画 ── */
.view-fade-enter-active,
.view-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.view-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.view-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
