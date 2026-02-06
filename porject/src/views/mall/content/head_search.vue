<template>
  <div class="search-container-wrapper">
    <div class="search-container">
      <div class="search-icon-wrapper">
        <el-icon class="search-icon"><Search /></el-icon>
      </div>
      <el-input
        v-model="inputValue"
        placeholder="搜索商品、品牌、店铺..."
        clearable
        @keyup.enter="handleSearch"
        class="search-input"
      />
      <el-button
        type="primary"
        @click="handleSearch"
        class="search-button"
      >
        <el-icon class="button-icon"><Search /></el-icon>
        搜索
      </el-button>
    </div>
    <div class="search-tags" v-if="hotTags.length">
      <span class="tags-label">热门搜索：</span>
      <el-tag
        v-for="tag in hotTags"
        :key="tag"
        size="small"
        class="hot-tag"
        @click="inputValue = tag"
      >
        {{ tag }}
      </el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

defineOptions({
  name: 'HeadSearch',
})

const inputValue = ref('')
const hotTags = ref(['手机', '电脑', '服装', '家居', '美妆'])

const handleSearch = () => {
  if (inputValue.value.trim()) {
    console.log('搜索内容:', inputValue.value)
  }
}
</script>

<style scoped>
.search-container-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  background: transparent;
  margin: 0;
}

.search-container {
  display: flex;
  align-items: center;
  width: 70%;
  max-width: 600px;
  background: var(--vt-c-white);
  border-radius: 24px;
  overflow: hidden;
  border: 2px solid #dcdfe6;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.search-container:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: #409EFF;
}

.search-container:focus-within {
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  border-color: #409EFF;
  border-width: 2px;
}

.search-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  color: var(--vt-c-text-light-2);
}

.search-icon {
  font-size: 16px;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
}

.search-input :deep(.el-input__wrapper) {
  border: none;
  background: transparent;
  box-shadow: none;
  padding: 0;
}

.search-input :deep(.el-input__inner) {
  border: none;
  background: transparent;
  height: 44px;
  font-size: 14px;
  color: var(--vt-c-text-light-1);
  padding: 0;
}

.search-input :deep(.el-input__inner::placeholder) {
  color: var(--vt-c-text-light-2);
  font-size: 14px;
}

.search-button {
  border-radius: 0;
  padding: 0 24px;
  height: 44px;
  font-size: 14px;
  background-color: #409EFF;
  border: none;
  color: white;
  transition: all 0.3s ease;
}

.search-button:hover {
  background-color: #3a8ee6;
}

.button-icon {
  margin-right: 4px;
  font-size: 14px;
}

.search-tags {
  display: flex;
  align-items: center;
  margin-top: 12px;
  flex-wrap: wrap;
  gap: 6px;
}

.tags-label {
  color: var(--vt-c-text-light-2);
  font-size: 13px;
  margin-right: 8px;
}

.hot-tag {
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid var(--color-border);
  background: var(--vt-c-white);
  font-size: 12px;
}

.hot-tag:hover {
  background: #409EFF;
  color: white;
  border-color: #409EFF;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-container-wrapper {
    padding: 15px 0;
  }

  .search-container {
    width: 90%;
    max-width: none;
  }

  .search-input :deep(.el-input__inner) {
    height: 40px;
    font-size: 13px;
  }

  .search-button {
    height: 40px;
    padding: 0 20px;
    font-size: 13px;
  }

  .search-tags {
    justify-content: center;
    margin-top: 10px;
  }
}

@media (max-width: 480px) {
  .search-container {
    width: 95%;
  }

  .search-icon-wrapper {
    padding: 0 12px;
  }

  .search-button {
    padding: 0 16px;
  }

  .button-text {
    display: none;
  }
}

/* 暗色模式适配 */
@media (prefers-color-scheme: dark) {
  .search-container {
    background: var(--vt-c-black);
    border-color: var(--vt-c-divider-dark-1);
  }

  .search-input :deep(.el-input__inner) {
    color: var(--vt-c-text-dark-1);
  }

  .search-input :deep(.el-input__inner::placeholder) {
    color: var(--vt-c-text-dark-2);
  }

  .search-icon-wrapper {
    color: var(--vt-c-text-dark-2);
  }

  .tags-label {
    color: var(--vt-c-text-dark-2);
  }
}

html.dark .search-container {
  background: var(--vt-c-black);
  border-color: var(--vt-c-divider-dark-1);
}

html.dark .search-container:hover {
  border-color: #409EFF;
}

html.dark .search-container:focus-within {
  border-color: #409EFF;
}

html.dark .search-container {
  background: var(--vt-c-black);
  border-color: var(--vt-c-divider-dark-1);
}

html.dark .search-input :deep(.el-input__inner) {
  color: var(--vt-c-text-dark-1);
}

html.dark .search-input :deep(.el-input__inner::placeholder) {
  color: var(--vt-c-text-dark-2);
}

html.dark .search-icon-wrapper {
  color: var(--vt-c-text-dark-2);
}

html.dark .tags-label {
  color: var(--vt-c-text-dark-2);
}
</style>
