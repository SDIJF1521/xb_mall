<template>
    <el-row :gutter="20">
        <el-col :span="16"><div class="grid-content ep-bg-purple"><h2>小白的商城</h2></div></el-col>
        <el-col :span="8">
              <div class="grid-content ep-bg-purple">
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
        </el-col>
        
    </el-row>
</template>
<script>
    export default{
        name:'HeadTrolley',
        data() {
            return{
                inputValue:''
            }
        },
        methods: {
        handleSearch() {
        if (this.inputValue.trim()) {
            console.log('搜索内容:', this.inputValue);
            }
        }
    }
}
</script>

<style>
.el-row {
  margin-bottom: 20px;
}
.el-row:last-child {
  margin-bottom: 0;
}
.el-col {
  border-radius: 4px;
}

.grid-content {
  border-radius: 4px;
  min-height: 40px;
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
</style>
