<template>
  <div class="search-container-wrapper">
    <div class="search-container">
      <el-input
        v-model="inputValue"
        placeholder="请输入搜索内容"
        clearable
        @keyup.enter="handleSearch"
        class="search-input"
      />
      <el-button
        type="primary"
        icon="Search"
        @click="handleSearch"
        class="search-button"
      >
        搜索
      </el-button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HeadSearch',
  data() {
    return {
      inputValue: ''
    };
  },
  methods: {
    handleSearch() {
      if (this.inputValue.trim()) {
        console.log('搜索内容:', this.inputValue);
      }
    }
  }
};
</script>

<style scoped>
.search-container-wrapper {
  display: flex;
  justify-content: center; /* 水平居中 */
  padding: 20px 0;
}

.search-container {
  display: flex;
  width: 70%; /* 占据父容器70%宽度 */
  max-width: 600px; /* 最大宽度限制，避免过大屏幕下过宽 */
  border-radius: 24px;
  overflow: hidden;
  border: 1px solid #dcdfe6;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.search-input {
  flex: 1;
  border: none;
  box-shadow: none;
  
  .el-input__inner {
    border: none;
    border-radius: 0;
    height: 44px;
    padding: 0 18px;
    font-size: 14px;
  }
}

.search-button {
  border-radius: 0;
  padding: 0 24px;
  height: 44px;
  font-size: 14px;
  background-color: #409eff;
  border-color: #409eff;
  
  &:hover {
    background-color: #3a8ee6;
    border-color: #3a8ee6;
  }
}
</style>