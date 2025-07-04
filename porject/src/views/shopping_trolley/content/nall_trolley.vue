<template>
    <el-empty description="购物车空空如也">
        <router-link to="/mall" class="router-button">
            <el-button type="primary">返回商城</el-button>
        </router-link>
    </el-empty>

</template>
<script>
export default {
    name:'NallTrolley'
}
</script>
<style scoped>
.router-button {
  text-decoration: none; /* 移除链接下划线 */
}
</style>