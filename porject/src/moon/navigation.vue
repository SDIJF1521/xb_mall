<template>
  <el-menu
    :default-active="activeIndex"
    class="el-menu-demo"
    mode="horizontal"
    @select="handleSelect"
  >
    <!-- 首页 -->
    <router-link to="/" custom>
      <template #default="{ navigate, isActive }">
        <el-menu-item 
          :class="{ 'is-active': isActive }"
          @click="navigate"
          index="1"
        >
          首页
        </el-menu-item>
      </template>
    </router-link>
    
    <!-- 商城 -->
    <router-link to="/mall" custom>
      <template #default="{ navigate, isActive }">
        <el-menu-item 
          :class="{ 'is-active': isActive }"
          @click="navigate"
          index="2"
        >
          商城
        </el-menu-item>
      </template>
    </router-link>
    
    <!-- 购物车 -->
    <router-link to="/shopping_trolley" custom>
      <template #default="{ navigate, isActive }">
        <el-menu-item 
          :class="{ 'is-active': isActive }"
          @click="navigate"
          index="3"
        >
          购物车
        </el-menu-item>
      </template>
    </router-link>
    
    <!-- 其他 -->
    <el-sub-menu index="4">
      <template #title>其他</template>
      <router-link to="/personal_center" custom>
        <template #default="{ navigate, isActive }">
          <el-menu-item 
            :class="{ 'is-active': isActive }"
            @click="navigate"
            index="4-1"
          >
            个人主页
          </el-menu-item>
        </template>
      </router-link>
      <el-menu-item index="null" disabled>
        <el-switch
          v-model="darkMode"
          class="theme-switch"
          active-text="黑夜模式"
          inactive-text="白天模式"
          style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
          @change="toggleTheme"
        />
      </el-menu-item>
    </el-sub-menu>
  </el-menu>
</template>

<script>
import { ref, computed } from 'vue';
import { useRoute } from 'vue-router';

export default {
  name: 'AppNavigation',
  setup() {
    // 获取当前路由
    const route = useRoute();
    
    // 状态管理
    const darkMode = ref(false);
    const isTransitioning = ref(false);
    
    // 计算当前激活的菜单项
    const activeIndex = computed(() => {
      switch (route.path) {
        case '/': return '1';
        case '/mall': return '2';
        case '/shopping_trolley': return '3';
        case '/personal_center': return '4-1';
        default: return '';
      }
    });
    
    // 处理菜单项选择事件
    const handleSelect = (key, keyPath) => {
      // 可根据需要添加额外逻辑
      console.log('选中菜单项:', key);
    };
    
    // 切换主题
    const toggleTheme = (value) => {
      isTransitioning.value = true;
      document.documentElement.classList.add('theme-transition');
      
      if (value) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      
      setTimeout(() => {
        isTransitioning.value = false;
        document.documentElement.classList.remove('theme-transition');
      }, 300);
      
      // 保存主题设置到本地存储
      localStorage.setItem('theme', value ? 'dark' : 'light');
    };
    
    // 初始化时恢复主题设置
    const initTheme = () => {
      const savedTheme = localStorage.getItem('theme');
      
      if (savedTheme === 'dark') {
        darkMode.value = true;
        document.documentElement.classList.add('dark');
      }
    };
    
    // 初始化
    initTheme();
    
    return {
      darkMode,
      isTransitioning,
      activeIndex,
      handleSelect,
      toggleTheme
    };
  }
}
</script>

<style scoped>
/* 主题切换开关样式 */
.theme-switch {
  margin-left: 20px;
}

/* 菜单居中显示 */
.el-menu {
  justify-content: center;
}

/* 激活状态样式 */
.is-active {
  color: #409EFF !important;
  font-weight: bold;
  border-bottom: 2px solid #409EFF;
}

/* 过渡动画效果 */
.theme-transition,
.theme-transition .el-header,
.theme-transition .el-footer,
.theme-transition .el-aside,
.theme-transition .el-main,
.theme-transition .el-menu,
.theme-transition .el-menu-item {
  transition: background-color 0.3s ease, color 0.3s ease;
}

.theme-transition .el-main {
  transition: all 0.3s ease;
  opacity: 0.98;
}
</style>