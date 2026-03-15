<template>
  <div class="head-trolley">
    <div class="head-left">
      <h2 class="head-title">小白的商城</h2>
    </div>
    <div class="head-right">
      <div class="search-container">
        <el-icon class="search-icon"><Search /></el-icon>
        <el-input
          :model-value="searchKeyword"
          @update:model-value="$emit('update:searchKeyword', $event)"
          placeholder="搜索购物车商品..."
          clearable
          @keyup.enter="handleSearch"
          class="search-input"
        />
        <el-button type="primary" @click="handleSearch" class="search-button">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'

defineOptions({ name: 'HeadTrolley' })

withDefaults(
  defineProps<{
    searchKeyword?: string
  }>(),
  { searchKeyword: '' }
)

const emit = defineEmits<{
  (e: 'update:searchKeyword', value: string): void
  (e: 'search'): void
}>()

const handleSearch = () => {
  emit('search')
}
</script>

<style scoped lang="scss">
.head-trolley {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  gap: 24px;
  flex-wrap: wrap;
}

.head-left {
  flex-shrink: 0;
}

.head-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--vt-c-text-light-1);
  margin: 0;
}

.head-right {
  flex: 1;
  min-width: 200px;
  display: flex;
  justify-content: flex-end;
}

.search-container {
  display: flex;
  align-items: center;
  width: 100%;
  max-width: 420px;
  background: var(--color-background);
  border-radius: 24px;
  overflow: hidden;
  border: 2px solid var(--color-border);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.search-container:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: #409eff;
}

.search-container:focus-within {
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  border-color: #409eff;
}

.search-icon {
  padding: 0 14px;
  color: var(--vt-c-text-light-2);
  font-size: 16px;
}

.search-input {
  flex: 1;
}

.search-input :deep(.el-input__wrapper) {
  border: none;
  background: transparent;
  box-shadow: none;
  padding: 0 8px 0 0;
}

.search-input :deep(.el-input__inner) {
  border: none;
  background: transparent;
  height: 40px;
  font-size: 14px;
}

.search-button {
  border-radius: 0;
  padding: 0 20px;
  height: 40px;
  font-size: 14px;
  border: none;
}

/* 暗色模式 */
html.dark .head-title {
  color: #fff;
}

html.dark .search-container {
  background: #252525;
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .search-container:hover,
html.dark .search-container:focus-within {
  border-color: #409eff;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.15);
}

html.dark .search-icon {
  color: rgba(255, 255, 255, 0.5);
}

html.dark .search-input :deep(.el-input__inner) {
  color: #fff !important;
}

html.dark .search-input :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.4) !important;
}
</style>
