<template>
  <div class="management-navigation">
    <div class="brand">
      <img src="@/assets/logo.jpg" alt="logo" class="brand-logo" />
      <h2 :class="titleColor">xb商城后台</h2>
    </div>

    <el-menu
      :default-active="activeIndex"
      class="el-menu-center"
      mode="horizontal"
      @select="handleSelect"
    >
      <el-menu-item v-if="pDash" index="1">仪表盘</el-menu-item>
      <el-menu-item v-if="pCommodity" index="2">商品管理</el-menu-item>
      <el-menu-item v-if="pUser" index="3">用户管理</el-menu-item>
      <el-menu-item v-if="pPromotion" index="6">营销管理</el-menu-item>
      <el-menu-item v-if="pRefund" index="5">纠纷管理</el-menu-item>
      <el-menu-item v-if="pCommodity" index="4">设置</el-menu-item>
    </el-menu>
    <el-switch
      v-model="value"
      size="large"
      active-text="黑夜模式"
      :active-action-icon="Moon"
      :inactive-action-icon="Sunny"
      inactive-text="白天模式"

      class="switch-left"
    />
  </div>
</template>

<script lang="ts" setup>
import { onMounted, ref, watch, computed } from 'vue';
import router from '@/router';
import { useRoute } from 'vue-router';
import { Sunny, Moon } from '@element-plus/icons-vue'
import {
  hasAdminPermission,
  hasAnyAdminPermission,
  canEnterManageHome,
} from '@/utils/adminPermission';
import { ElMenuItem } from 'element-plus';

const pDash = computed(() => canEnterManageHome());
const pCommodity = computed(() =>
  hasAnyAdminPermission(['admin.commodity', 'admin.commodity_apply']),
);
const pUser = computed(() =>
  hasAnyAdminPermission([
    'admin.user.merchant',
    'admin.user.mall',
    'admin.user.platform',
    'admin.user.role',
  ]),
);
const pPromotion = computed(() => hasAdminPermission('admin.promotion'));
const pRefund = computed(() => hasAdminPermission('admin.refund'));

const activeIndex = ref('')

// 处理菜单选择事件
const handleSelect = (index: string) => {
  if (index === '1') router.push('/management');
  else if (index === '2') router.push('/management_commodity');
  else if (index === '3') router.push('/user_management');
  else if (index === '4') router.push('/management_system_settings');
  else if (index === '5') router.push('/management_refund');
  else if (index === '6') router.push('/management_promotion');
}

// 定义组件名称
defineOptions({
    name: 'ManagementNavigation',
})


// 定义一个开关状态
const value = ref(true)

const route = useRoute();

function syncNav(path: string) {
  if (path === '/management') activeIndex.value = '1';
  else if (path.startsWith('/management_commodity') || path.startsWith('/management_commodity_apply'))
    activeIndex.value = '2';
  else if (
    path.startsWith('/user_management') ||
    path.startsWith('/audit_apply_seller') ||
    path.startsWith('/business_management')
  )
    activeIndex.value = '3';
  else if (path.startsWith('/management_system_settings'))
    activeIndex.value = '4';
  else if (path.startsWith('/management_refund'))
    activeIndex.value = '5';
  else if (path.startsWith('/management_promotion'))
    activeIndex.value = '6';
}

watch(
  () => route.path,
  (p) => syncNav(p),
  { immediate: true },
);

onMounted(()=>{
    const savedTheme =  localStorage.getItem('management_theme')
    if (savedTheme === 'dark') {
        value.value = true;
        document.documentElement.classList.add('dark');
      } else if (!savedTheme){
        document.documentElement.classList.add('dark');
        localStorage.setItem('management_theme', 'dark')
      }else{
        value.value = false;
        document.documentElement.classList.remove('dark');
      }
})
const titleColor = ref(value.value ? 'title_night' : 'title_daytime')
// 监听开关状态变化
watch(value, (newValue) => {
    if (newValue) {
        document.documentElement.classList.add('dark');
        localStorage.setItem('management_theme', 'dark')
    } else {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('management_theme', 'light')
    }
    titleColor.value = value.value ? 'title_night' : 'title_daytime'
})

// 标题颜色函数


// 开关触发函数
const toggLeTheme = ref()
</script>

<style scoped>
.management-navigation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.brand-logo {
  height: 36px;
  width: 36px;
  border-radius: 8px;
  object-fit: cover;
}

.el-menu-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.switch-left {
  margin-right: 20px;
}
.title_daytime{
    color: #000;
}
.title_night{
    background: linear-gradient(to right, #46e2cb, #742bd9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
}
</style>
