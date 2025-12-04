<template>
    <div class="header-div">
    <div>
        欢迎回来:{{ data.userName }}
    </div>
    <el-input
        style="width: 240px;"
        v-model="input"
        placeholder="搜索"
        :prefix-icon="Search"
        clearable
    />

    <div class="header-content">
        <el-avatar size="large" :src="data.img" />
        <div>
            <div style="display: flex; gap: 15px;">
                <el-badge>
                    <el-button :icon="Bell" size="small" circle />
                </el-badge>
                <el-badge>
                    <el-button :icon="ChatDotRound" size="small" circle />
                </el-badge>
            </div>
            <el-text>昵称:{{ data.userName }}</el-text>
        </div>
    </div>
</div>
</template>
<script lang="ts" setup>
import {ref } from 'vue'
import {Bell,ChatDotRound,Search} from '@element-plus/icons-vue'

defineOptions({
    name: "BuyerHead"
})
const input = ref('')
const value = ref('')
const user = localStorage.getItem('buyer_user')
// oxlint-disable-next-line no-constant-binary-expression
const data = ref({'img':`data:image/png;base64,${localStorage.getItem('img')}`||'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png','userName':user||'小白'})

</script>
<style scoped>
    .header-content{
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 10px;
    }
    .header-div{
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
    }
</style>
