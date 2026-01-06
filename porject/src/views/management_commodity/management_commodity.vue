<template>
<el-container>
    <ManagementNavigation/>
    <el-container>
      <el-aside width="200px">
        <el-menu
        :default-active="activeIndex"
        class="el-menu-vertical-demo"
        @select="handleMenuSelect"
        >
          <!-- 商品审核 -->
          <el-menu-item index="1">
            <el-icon><DocumentChecked /></el-icon>
            <template #title>商品审核</template>
          </el-menu-item>

          <!-- 商品列表 -->
          <el-menu-item index="2">
            <el-icon><List /></el-icon>
            <template #title>商品列表</template>
          </el-menu-item>

          <!-- 商品分类 -->
          <el-menu-item index="3">
            <el-icon><Grid /></el-icon>
            <template #title>商品分类</template>
          </el-menu-item>

          <!-- 违规商品 -->
          <el-menu-item index="4">
            <el-icon><Warning /></el-icon>
            <template #title>违规商品</template>
          </el-menu-item>

          <!-- 商品统计 -->
          <el-menu-item index="5">
            <el-icon><TrendCharts /></el-icon>
            <template #title>商品统计</template>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <el-main>
        <component :is="mods"/>
      </el-main>
    </el-container>

    
  <el-footer class="footer-content">版权所有 © [小白的商城]，保留所有权利。</el-footer>
</el-container>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ManagementNavigation from '@/moon/management_navigation.vue'
import CommodityAudit from './content/commodity_audit.vue'
import {
  DocumentChecked,
  List,
  Grid,
  Warning,
  TrendCharts
} from '@element-plus/icons-vue'

const mods = ref('CommodityAudit')
const activeIndex = ref('1') // 默认选中商品列表

// 菜单选择处理函数
const handleMenuSelect = (index: string) => {
  activeIndex.value = index

  // 根据菜单项跳转到不同子页面或切换内容区域
}



defineOptions({
  name:'ManagementCommodity',
  components:{
    ManagementNavigation,
    DocumentChecked,
    List,
    Grid,
    Warning,
    TrendCharts,
    CommodityAudit
  }
})
</script>
<style scoped>
.footer-content {
  text-align: center;
  color: darkgray;
}

.el-main {
  padding: 20px;
  flex: 1;
}

:deep() .el-main {
  border: 2px solid transparent;
  border-image: linear-gradient(to right, #383e4b, #3d3545) 1;
}

.el-menu-vertical-demo {
  border-right: none;
  height: calc(100vh - 120px);
  padding: 20px 10px;
}

.el-menu-vertical-demo .el-menu-item {
  height: 48px;
  line-height: 48px;
  margin-bottom: 8px;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
  position: relative;
}

.el-menu-vertical-demo .el-menu-item:hover {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  transform: translateX(4px);
}

.el-menu-vertical-demo .el-menu-item.is-active {
  background-color: var(--el-color-primary);
  color: white;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.el-menu-vertical-demo .el-menu-item.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 24px;
  background-color: white;
  border-radius: 2px;
}

.el-menu-vertical-demo .el-icon {
  margin-right: 8px;
  font-size: 16px;
}

/* 暗色主题适配 */
.dark .el-menu-vertical-demo .el-menu-item:hover {
  background-color: rgba(64, 158, 255, 0.1);
  color: #409eff;
}

.dark .el-menu-vertical-demo .el-menu-item.is-active {
  background-color: #409eff;
  color: white;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.4);
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .el-menu-vertical-demo {
    padding: 10px 5px;
  }

  .el-menu-vertical-demo .el-menu-item {
    height: 44px;
    line-height: 44px;
    font-size: 13px;
  }
}

</style>

