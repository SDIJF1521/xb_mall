<template>
  <el-container>
    <el-header>
      <h3 class="title">{{title}}</h3>
    </el-header>
    <el-main>
      <div v-for="(component, index) in currentComponents" :key="index" class="component-container">
        <component :is='component'></component>
      </div>
    </el-main>
    <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
  </el-container>
</template>

<script setup lang="ts">
import {ref,onMounted} from 'vue'
import { useRoute } from 'vue-router'
import BuyerTheme from '@/moon/buyer_theme';
import RoleRatio from '@/views/buyer_user_statistics/content/role_ratio.vue'
import UserListMain from '@/views/buyer_user_list_id/content/user_list_main.vue'
import RoleListMain from '@/views/buyer_role_list/content/role_list_main.vue'
import CommodityAdd from '@/views/buyer_commodity_add/content/commodity_add.vue'

defineOptions({
    name: 'BuyerTemplate',
    components: {
        BuyerTheme,
        UserListMain,
        RoleRatio,
        RoleListMain,
        CommodityAdd,
    }
})

const props = defineProps({
  currentComponents: {
    type: Array as () => string[], // 接收组件名列表
    default: () => ['Statistic'],
  }
})

const route = useRoute()
const title = ref('')

onMounted(() => {
  new BuyerTheme().toggleTheme(true)
  console.log('当前路由路径:', route.path);

  // 根据当前路由路径设置页面标题
  console.log('完整路由对象:', route);
  console.log('路由路径:', route.path);
  console.log('路由名称:', route.name);
  console.log('设置标题前的值:', title.value);

  if (route.path.startsWith('/buyer_user_list_id')) {
    title.value = '小白的商城-用户管理页';
    console.log('设置用户管理页标题，新值:', title.value);
  } else if (route.path.startsWith('/buyer_role_list')) {
    title.value = '小白的商城-角色管理页';
    console.log('设置角色管理页标题，新值:', title.value);
  } else if (route.path.startsWith('/buyer_user_statistics')) {
    title.value = '小白的商城-用户统计页';
    console.log('设置用户统计页标题，新值:', title.value);
  }else if (route.path.startsWith('/buyer_commodity_add')) {
    title.value = '小白的商城-商品添加页';
    console.log('设置商品添加页标题，新值:', title.value);
  }else {
    title.value = '小白的商城';
    console.log('设置默认标题，新值:', title.value);
  }

  // 强制更新视图
  setTimeout(() => {
    console.log('延迟后标题值:', title.value);
  }, 100);
})
</script>

<style scoped>
/* 组件容器样式 - 细线边框 + 悬浮效果 */
.component-container {
  margin-bottom: 24px;
  padding: 20px;
  border: 1px solid #656668;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

/* 悬浮效果 */
.component-container:hover {
  border-color: #409eff;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

/* 细线装饰效果 */
.component-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #409eff 0%, #67c23a 50%, #e6a23c 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.component-container:hover::before {
  opacity: 0.8;
}

.component-container:last-child {
  margin-bottom: 0;
}

/* 响应式间距调整 */
@media (max-width: 768px) {
  .component-container {
    margin-bottom: 16px;
    padding: 16px;
    border-radius: 6px;
  }

  .component-container:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 12px rgba(64, 158, 255, 0.12);
  }
}

@media (max-width: 480px) {
  .component-container {
    margin-bottom: 12px;
    padding: 12px;
    border-radius: 4px;
  }

  .component-container:hover {
    transform: translateY(-0.5px);
    box-shadow: 0 1px 8px rgba(64, 158, 255, 0.1);
  }

  .component-container::before {
    height: 2px;
  }
}

.footer-content {
    text-align: center;
    padding: 10px 0;
}

.el-header {
  border-bottom: 1px solid #e0e0e0;
  padding: 0 20px;
  display: flex;
  align-items: center; /* 垂直居中 */
  justify-content: space-between; /* 左右分布对齐 */
}

.title {
  background: linear-gradient(to right, #7ef0b3, #9c6edd);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}
</style>
