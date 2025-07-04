<template>
<div class="not-found">
<el-result
icon="warning"
title="404"
sub-title="抱歉，您访问的页面不存在！"
>
<template #extra>
<el-button type="primary" @click="goHome">返回首页</el-button>
</template>
</el-result>
</div>
</template>

<script>
import { ref, computed } from 'vue';
import { ElResult, ElButton } from "element-plus";

export default {
    name: "NotFound",

    components: {
        ElResult,
        ElButton,
    },
    methods: {
        goHome() {
            this.$router.push("/");
        },
    },
    setup() {
        const darkMode = ref(false);
        const initTheme = () => {
        const savedTheme = localStorage.getItem('theme');
        
        if (savedTheme === 'dark') {
            darkMode.value = true;
            document.documentElement.classList.add('dark');
        }
        };
        // 初始化
        initTheme();
    }
}
</script>

<style scoped>
    .not-found {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    }
</style>