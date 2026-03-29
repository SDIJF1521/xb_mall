<template>
  <el-container>
    <el-container>
      <BuyerNavigation />
      <el-container>
        <el-header>
          <BuyerHead />
        </el-header>
        <el-main class="promo-main">
          <el-container class="promo-container">
            <el-aside width="240px" class="promo-aside">
              <div class="aside-header">
                <el-icon class="aside-header__icon"><Ticket /></el-icon>
                <span class="aside-header__text">营销管理</span>
              </div>

              <div v-if="isOwner && storeList.length > 1" class="store-selector">
                <div class="store-selector__label">当前店铺</div>
                <el-select
                  v-model="selectedMallId"
                  placeholder="选择店铺"
                  size="default"
                  style="width: 100%"
                  @change="onStoreChange"
                >
                  <el-option
                    v-for="s in storeList"
                    :key="s.id"
                    :label="s.mall_name"
                    :value="s.id"
                  />
                </el-select>
              </div>
              <div v-else-if="isOwner && storeList.length === 1" class="store-selector">
                <div class="store-selector__label">当前店铺</div>
                <div class="store-selector__name">{{ storeList[0].mall_name }}</div>
              </div>

              <el-menu
                :default-active="activeIndex"
                class="promo-menu"
                @select="handleMenuSelect"
              >
                <el-menu-item index="1">
                  <el-icon><Ticket /></el-icon>
                  <span>优惠券管理</span>
                </el-menu-item>
                <el-menu-item index="2">
                  <el-icon><Lightning /></el-icon>
                  <span>店铺活动</span>
                </el-menu-item>
                <el-menu-item index="3">
                  <el-icon><Star /></el-icon>
                  <span>平台活动</span>
                </el-menu-item>
              </el-menu>
            </el-aside>

            <el-main class="promo-content">
              <transition name="view-fade" mode="out-in">
                <component :is="currentView" :key="activeIndex + '-' + selectedMallId" :mall-id="selectedMallId" />
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
import axios from 'axios'
import { Ticket, Lightning, Star } from '@element-plus/icons-vue'
import BuyerHead from '@/moon/buyer_head.vue'
import BuyerNavigation from '@/moon/buyer_navigation.vue'
import BuyerTheme from '@/moon/buyer_theme'
import BuyerCouponManage from './content/BuyerCouponManage.vue'
import BuyerActivityManage from './content/BuyerActivityManage.vue'
import BuyerJoinActivity from './content/BuyerJoinActivity.vue'

defineOptions({ name: 'BuyerPromotionManage' })

const API = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

const activeIndex = ref('1')
const currentView = shallowRef(BuyerCouponManage)

const isOwner = ref(false)
const storeList = ref<{ id: number; mall_name: string }[]>([])
const selectedMallId = ref<number | null>(null)

function decodeTokenPayload(): Record<string, any> | null {
  const token = localStorage.getItem('buyer_access_token')
  if (!token) return null
  try {
    const parts = token.split('.')
    if (parts.length < 2) return null
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
    return payload
  } catch {
    return null
  }
}

async function loadStoreList() {
  const payload = decodeTokenPayload()
  if (!payload) return

  const station = payload.station ?? payload.Station
  if (String(station) === '1') {
    isOwner.value = true
    const token = localStorage.getItem('buyer_access_token') || ''
    try {
      const formData = new FormData()
      formData.append('token', token)
      const { data } = await API.post('/get_mall_name', formData)
      if (data.current && data.mall_name?.length) {
        storeList.value = data.mall_name
        selectedMallId.value = data.mall_name[0].id
      }
    } catch { /* ignore */ }
  }
}

function onStoreChange() {
  const view = currentView.value
  currentView.value = null as any
  setTimeout(() => { currentView.value = view }, 0)
}

function handleMenuSelect(index: string) {
  activeIndex.value = index
  switch (index) {
    case '1':
      currentView.value = BuyerCouponManage
      break
    case '2':
      currentView.value = BuyerActivityManage
      break
    case '3':
      currentView.value = BuyerJoinActivity
      break
    default:
      currentView.value = BuyerCouponManage
  }
}

onMounted(async () => {
  new BuyerTheme().initTheme()
  await loadStoreList()
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

.promo-main {
  padding: 0;
}

.promo-container {
  height: calc(100vh - 130px);
}

.promo-aside {
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

.store-selector {
  padding: 14px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);

  &__label {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-bottom: 8px;
    font-weight: 500;
  }

  &__name {
    font-size: 14px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    padding: 6px 0;
  }
}

.promo-menu {
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

.promo-content {
  padding: 24px 28px;
  overflow-y: auto;
  background: var(--el-fill-color-blank);
}

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
