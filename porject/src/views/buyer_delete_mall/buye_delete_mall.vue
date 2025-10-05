<template>
    <el-container>
        <el-header>
            <div class="management-navigation">
                <h2 class="title_night">小白的商城-店铺删除页</h2>
            </div>
        </el-header>
        <el-main>
            
        </el-main>
        <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
    </el-container>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import BuyerTheme from '@/moon/buyer_theme';

// 定义组件名称
defineOptions({
    name: 'BuyerDeleteMall'
})

// 初始化主题
onMounted(()=>{
    new BuyerTheme().toggleTheme(true);
})
</script>
<style scoped>
.footer-content {
    font-size: 14px;
    color: #999;
    text-align: center;
    padding: 20px 0;
}

.management-navigation {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 0 20px;
}
.title_night{
    background: linear-gradient(to right, #dc5127, #9c6edd);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    color: transparent;
}
.title_daytime{
    color: #000;
}

.el-header {
    border-bottom: 1px solid #575859;
    padding-bottom: 10px;
    margin-bottom: 10px;
}
</style>