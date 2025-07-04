<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <!-- 使用注册的组件名称 -->
        <AppNavigation/>
      </el-header>
      <el-header> <!-- 修正：el-header -->
        <HodeTrolley/>
      </el-header>
      <el-main>
        <component :is="mods"></component> <!-- 使用v-bind语法 -->
      </el-main>
      <el-footer class="footer-content">版权所有 © [小白的商城]，保留所有权利。</el-footer>
    </el-container>
  </div>
</template>
<script>
import AppNavigation from '@/moon/navigation.vue';
import NallTrolley from './content/nall_trolley.vue'
import HodeTrolley from './content/head_trolley.vue'
export default {
  name: 'ShoppingTrolley',
  data() {
    return {
      mods: 'NallTrolley' // 返回一个对象，包含mods属性
    }
  },
  components: {
    AppNavigation,
    NallTrolley,
    HodeTrolley
  },
}
</script>
<style scoped>
.footer-content {
  text-align: center; /* 文字内容水平居中 */
  color: darkgray;
}
</style>