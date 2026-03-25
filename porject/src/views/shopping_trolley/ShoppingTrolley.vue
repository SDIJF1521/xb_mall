<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <AppNavigation/>
      </el-header>
      <el-header>
        <HodeTrolley v-model:search-keyword="searchKeyword" @search="onCartSearch" />
      </el-header>
      <el-main class="trolley-main">
        <NallTrolley ref="nallTrolleyRef" :search-keyword="searchKeyword" />
      </el-main>
      <el-footer class="footer-content">版权所有 © [xb商城]，保留所有权利。</el-footer>
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
      searchKeyword: ''
    }
  },
  components: {
    AppNavigation,
    NallTrolley,
    HodeTrolley
  },
  methods: {
    onCartSearch() {
      this.$refs.nallTrolleyRef?.fetchList?.()
    }
  }
}
</script>
<style scoped>
.trolley-main {
  padding: 20px 24px;
  min-height: 60vh;
  background: var(--color-background-soft);
}

.footer-content {
  text-align: center;
  color: var(--vt-c-text-light-2);
}

html.dark .trolley-main {
  background: #1a1a1a;
}

html.dark .footer-content {
  color: rgba(255, 255, 255, 0.5);
}
</style>
