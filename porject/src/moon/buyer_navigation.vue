<template>
        <el-menu
            :default-active="selected"
            :collapse="store.isMouseInside"
            @mouseenter="store.handleMouseLeave()"
            @mouseleave="store.handleMouseEnter()"
            @select="handleSelect"

        >
            <el-menu-item index="0" disabled>
                <el-icon><Eleme/></el-icon>

                <span slot="title">
                    欢迎来到买家端后台
                </span>

            </el-menu-item>

            <el-menu-item index="1">
                <el-icon><Odometer/></el-icon>
                <span slot="title">仪表盘</span>
            </el-menu-item>
            <el-menu-item index="2">
                <el-icon><Shop/></el-icon>
                <span slot='title'>店铺管理</span>
            </el-menu-item>
            <el-menu-item index="3">
                <el-icon><List/></el-icon>
                <span slot="title">订单管理</span>
            </el-menu-item>
            <el-menu-item index="4">
                <el-icon><Handbag/></el-icon>
                <span slot="title">商品管理</span>
            </el-menu-item>
            <el-menu-item index="5">
                <el-icon><User/></el-icon>
                <span slot="title">用户管理</span>
            </el-menu-item>
            <el-menu-item index="6">
                <el-badge :value="csUnreadCount" :hidden="csUnreadCount === 0" :max="99" class="cs-nav-badge">
                    <el-icon><Service/></el-icon>
                </el-badge>
                <span slot="title">客服管理</span>
            </el-menu-item>
            <el-menu-item index="7">
                <el-icon><DocumentCopy/></el-icon>
                <span slot="title">评论管理</span>
            </el-menu-item>
            <el-menu-item index="8">
                <el-icon><Box/></el-icon>
                <span slot="title">物流管理</span>
            </el-menu-item>
            <el-menu-item index = "9">
                <el-icon><Setting/></el-icon>
                <span slot="title">系统管理</span>

            </el-menu-item>

        </el-menu>


</template>

<style scoped>
.cs-nav-badge :deep(.el-badge__content) {
  background: #f56c6c;
}
</style>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import router from '@/router'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { Eleme, Odometer, Shop, List, Handbag, User, DocumentCopy, Box, Setting, Service } from '@element-plus/icons-vue'
import { useBuyerNavigationStore } from '@/moon/buyer_navigatiom_pinia'

const store = useBuyerNavigationStore()
const selected = ref('1')
const csUnreadCount = ref(0)
// 记录未读数最多的店铺 ID，便于快速跳转
let topUnreadMallId: number | null = null

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

async function fetchCsUnread() {
  const token = localStorage.getItem('buyer_access_token')
  if (!token) return
  try {
    const [totalRes, storeRes] = await Promise.all([
      Axios.get('/cs_seller_total_unread', { headers: { 'access-token': token } }),
      Axios.get('/cs_seller_store_unreads', { headers: { 'access-token': token } }),
    ])
    if (totalRes.data?.current && typeof totalRes.data.unread_count === 'number') {
      csUnreadCount.value = totalRes.data.unread_count
    }
    // 找到未读最多的店铺
    topUnreadMallId = null
    if (storeRes.data?.current && Array.isArray(storeRes.data.data)) {
      let maxCount = 0
      for (const item of storeRes.data.data) {
        if (item.unread_count > maxCount) {
          maxCount = item.unread_count
          topUnreadMallId = item.mall_id
        }
      }
    }
  } catch {
    // ignore
  }
}

let pollTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  fetchCsUnread()
  pollTimer = setInterval(fetchCsUnread, 30000) // 每30秒轮询
    const route = useRoute();
    switch (route.path) {
        case '/buyer_index':
            selected.value = '1'; break;
        case '/buyer_store_management':
            selected.value = '2'; break;
        case '/buyer_user_manage':
            selected.value = '5'; break;
        case '/buyer_commodity_management':
            selected.value = '4'; break;
        case '/buyer_cs_select':
            selected.value = '6'; break;
        default:
            if (route.path.startsWith('/buyer_customer_service')) {
                selected.value = '6';
            }
            break;
        case '/buyer_set':
            selected.value = '9';
            break;
    }
})

const handleSelect = (index: string) => {
    if (index === '1') {
        router.push('/buyer_index')
    } else if (index === '2') {
        router.push('/buyer_store_management')
    } else if (index === '4') {
        router.push('/buyer_commodity_management')
    } else if (index === '5') {
        router.push('/buyer_user_manage')
    } else if (index === '6') {
        // 有未读消息时直接跳转到未读最多的店铺客服页，否则进入店铺选择页
        if (topUnreadMallId) {
            router.push(`/buyer_customer_service/${topUnreadMallId}`)
        } else {
            router.push('/buyer_cs_select')
        }
    } else if (index === '9') {
        router.push('/buyer_set')
    }
}

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

defineOptions({
    name:'BuyerNavigation'})
</script>
