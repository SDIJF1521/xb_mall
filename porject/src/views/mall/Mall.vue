<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <!-- 使用注册的组件名称 -->
        <AppNavigation/>
      </el-header>
      <el-main>
        <!-- 通过计算属性动态切换组件 -->
        <HeadSearch/>
      </el-main>
      <el-container>
        <el-container>
          <el-main>
            <!-- 主内容区域，直接使用组件 -->
            <component :is="mods"></component>
          </el-main>
        </el-container>
      </el-container>
      <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
    </el-container>
  </div>
</template>

<script>
import AppNavigation from '@/moon/navigation.vue';
import HeadSearch from '@/views/mall/content/head_search.vue';
import NullPage from '@/views/mall/content/nall_page.vue';
import MallGoods from '@/views/mall/content/mall_goods.vue'

export default {
  name: 'Mall',
  data() {
    return {
      mods:'NullPage'
    }
  },
  components: {
    AppNavigation,
    HeadSearch,
    NullPage,
    MallGoods
  },
  methods: {
  }
}
</script>
<style scoped>
.footer-content {
  text-align: center; /* 文字内容水平居中 */
  color: darkgray;
}
</style>