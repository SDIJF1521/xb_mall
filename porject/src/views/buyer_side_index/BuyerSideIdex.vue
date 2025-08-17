<template>
    <el-container>
        <el-main>
            <el-row>
                    <BuyerNavigation/>
                <el-container>
                    <el-header>头部</el-header>
                    <el-main>
                        内容
                    </el-main>
                </el-container>
                    

            </el-row>

        </el-main>
        <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>

    </el-container>

</template>
<script lang="ts" setup>
import BuyerNavigation from '@/moon/buyer_navigation.vue'

 defineOptions({
    name:'BuyerSideIdex',
    components:{
        BuyerNavigation
    }


 })
</script>
<style scoped>
    .footer-content {
        text-align: center;
        color: darkgray;
        }
</style>