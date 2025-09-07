<template>
    <el-container>
        <el-container>
            <BuyerNavigation />
            <el-container>
                <el-header>
                    <BuyerHead/>
                </el-header>
                <el-main>
                    <div>
                        <el-select v-model="value" placeholder="Select" style="width: 240px">
                            <el-option
                            v-for="item in options"
                            :key="item.value"
                            :label="item.label"
                            :value="item.value"
                            />
                        </el-select>
                        <el-button type="primary" plain>导出报表</el-button>
                    </div>
                    <DataDisplay/>
                    <Sale/>
                </el-main>
            </el-container>
        </el-container>
        <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
    </el-container>
</template>
<script lang="ts" setup>
import { ref,onMounted } from 'vue'
import {Bell,ChatDotRound,Search} from '@element-plus/icons-vue'
import BuyerNavigation from '@/moon/buyer_navigation.vue'
import DataDisplay from './content/data_display.vue'
import Sale from './content/sale.vue'
import BuyerHead from '@/moon/buyer_head.vue'

const input = ref('')
const value = ref('')
const options = ref([
    { value: '最近一周', label: '最近一周' },
    { value: '最近一个月', label: '最近一个月' },
    { value: '最近三个月', label: '最近三个月' },
    { value: '最近一年', label: '最近一年' },
  ])

defineOptions({
    name:'BuyerSideIdex',
    components:{
        BuyerNavigation,
        DataDisplay,
        Sale,
        BuyerHead

    }


 })

onMounted(()=>{
    document.documentElement.classList.add('dark')
 })
 const data = ref({'img':'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png','userName':'小白'})

</script>
<style scoped>
    .footer-content {
        text-align: center;
        color: darkgray;
        }
    .el-header {
        border-bottom: 1px solid #514d4d;
        padding-bottom: 10px;
        margin-bottom: 10px;
    }
    .main-div{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
</style>