<template>
    <el-container>
        <el-main>内容</el-main>
        <el-footer class="footer-content">版权所有 © [小白的商城]，保留所有权利。</el-footer>
    </el-container>

</template>
<script setup lang="ts">
import {ref,onMounted} from 'vue'
import axios from 'axios';

const Axios = axios.create({
    baseURL:'http://127.0.0.1:8000/api',
    timeout:10000
})

defineOptions({name:'BuyerSideSing'})
</script>
<style scoped>
    .footer-content {
        text-align: center;
        color: darkgray;
        }
</style>