<template>

    <el-container>
      <el-header>
        <app-navigation/>
      </el-header>
      <el-main>
        <el-table  style="width: 100%"  v-infinite-scroll="loadMore">
            <el-table-column prop="date" label="省" />
            <el-table-column prop="name" label="市" />
            <el-table-column prop="address" label="县" />
            <el-table-column prop="address" label="详细地址" />
            <el-table-column prop="address" label="添加时间" />
            <el-table-column prop="address" label="操作">
                <template slot-scope="scope">
                    <el-button type="warning" plain>应用</el-button>
                    <el-button type="info" size="mini" plain>编辑</el-button>
                    <el-button type="danger" size="mini" plain>删除</el-button>
                </template>
            </el-table-column>
        </el-table>
        <el-drawer v-model="drawer" title="信息填写" >
            <el-form :model="form" label-width="auto" style="max-width: 600px">
                <el-form-item>
                    <el-select
                        v-model="form.save"
                        placeholder="省"
                        size="large"
                        style="width: 240px"
                    >

                    </el-select>
                </el-form-item>
            </el-form>
        </el-drawer>
      </el-main>
      <el-button type="primary" @click="add_addre">添加地址</el-button>
      <el-footer class="footer-content">版权所有 © [小白的商城]，保留所有权利。</el-footer>
    </el-container>

</template>
<script setup lang="ts">
import {ref,reactive} from 'vue'
import axios from 'axios';
import router from '@/router'
import AppNavigation from '@/moon/navigation.vue'
import { ElForm,ElFormItem,ElInput } from 'element-plus'

const form = reactive({
    'save':'',
    'city':'',
    'county':'',
    'detail_address':''
})

const drawer = ref(false)

const add_addre = ref(()=>{
    drawer.value = true
})
defineOptions({
    name:'AddreSet',
    components:{
        AppNavigation
    }
    })

const loadMore = ref(async()=>{})
</script>
<style scoped>
    .footer-content {
    text-align: center;
    color: darkgray;
    }
</style>