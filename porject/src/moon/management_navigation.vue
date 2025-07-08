<template>
  <div class="management-navigation">
    <h2 :class="titleColor">小白的个人商城后台</h2>
    
    <el-menu
      :default-active="activeIndex"
      class="el-menu-center"
      mode="horizontal"
       @select="handleSelect"
    >
      <el-menu-item index="1">仪表盘</el-menu-item>
      <el-menu-item index="2">商品管理</el-menu-item>
      <el-menu-item index="3">订单管理</el-menu-item>
      <el-menu-item index="4">用户管理</el-menu-item>
      <el-menu-item index="5">评论管理</el-menu-item>
      <el-menu-item index="6">数据统计</el-menu-item>
      <el-menu-item index="7">设置</el-menu-item>
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
import { onMounted, ref, watch } from 'vue';
import router from '@/router';
import { useRoute } from 'vue-router';
import { Sunny, Moon } from '@element-plus/icons-vue'

// 设置导航栏默认选中项
const activeIndex = ref('')

// 处理菜单选择事件
const handleSelect = (index: string) => {
  console.log('选中的菜单 index:', index);
  if (index =='1'){
    router.push('/management')
  }else if (index =='4'){
    router.push('/user_management')
  }
}

// 定义组件名称
defineOptions({
    name: 'ManagementNavigation',
})


// 定义一个开关状态
const value = ref(true)

onMounted(()=>{
  const route = useRoute()
  // 修正导航栏选项
  
    switch (route.path) {
      
      case '/management':
        activeIndex.value = '1'
        break
      case '/user_management':
        activeIndex.value = '4'
        break
    }
    
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