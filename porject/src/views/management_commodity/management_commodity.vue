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

          <!-- 申诉审核 -->
          <el-menu-item index="6">
            <el-icon><ChatLineSquare /></el-icon>
            <template #title>申诉审核</template>
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


  <el-footer class="footer-content">版权所有 © [xb商城]，保留所有权利。</el-footer>
</el-container>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import ManagementNavigation from '@/moon/management_navigation.vue'
import CommodityAudit from './content/commodity_audit.vue'
import CommodityList from './content/commodity_list.vue'
import CommodityClassify from './content/commodity_classify.vue'
import CommodityViolation from './content/commodity_violation.vue'
import CommodityAppealManage from './content/commodity_appeal.vue'
import CommodityStatistics from './content/commodity_statistics.vue'
import {
  DocumentChecked,
  List,
  Grid,
  Warning,
  ChatLineSquare,
  TrendCharts
} from '@element-plus/icons-vue'

const MENU_STORAGE_KEY = 'management_commodity_menu_index'

const indexToMods: Record<string, string> = {
  '1': 'CommodityAudit',
  '2': 'CommodityList',
  '3': 'CommodityClassify',
  '4': 'CommodityViolation',
  '5': 'CommodityStatistics',
  '6': 'CommodityAppealManage'
}

function getSavedIndex(): string {
  const saved = localStorage.getItem(MENU_STORAGE_KEY)
  return saved && indexToMods[saved] ? saved : '1'
}

const activeIndex = ref(getSavedIndex())
const mods = ref(indexToMods[activeIndex.value])

const handleMenuSelect = (index: string) => {
  activeIndex.value = index
  mods.value = indexToMods[index] || 'CommodityAudit'
  localStorage.setItem(MENU_STORAGE_KEY, index)
}

defineOptions({
  name:'ManagementCommodity',
  components:{
    ManagementNavigation,
    DocumentChecked,
    List,
    Grid,
    Warning,
    ChatLineSquare,
    TrendCharts,
    CommodityAudit,
    CommodityList,
    CommodityClassify,
    CommodityViolation,
    CommodityAppealManage,
    CommodityStatistics
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
<style>
/* 图片预览层需置于最上层，避免与表格/卡片固定列等冲突 */
.el-image-viewer__wrapper {
  z-index: 9999 !important;
}
</style>
