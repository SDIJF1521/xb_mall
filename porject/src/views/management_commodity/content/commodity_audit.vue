<template>
    <div style="display: flex; justify-content: center; margin-top: 20px; margin-bottom: 40px;">
        <el-input
            v-model="select"
            style="width: 240px; border-radius: 20px;"
            placeholder="搜索"
            :prefix-icon="Search"
            @keyup.enter="getCommodityAudit(1)"
            clearable
        />
    </div>
    <div v-if="commodity_audit_list.length == 0" class="empty-container">
        <el-empty description="暂无数据" />
    </div>
    <div v-else>
        <el-card v-for="item in commodity_audit_list" :key="item.shopping_id" class="glow-card">
            <el-descriptions title="商品信息" direction="vertical" border>
                <el-descriptions-item label="商品名称">{{ item.name }}</el-descriptions-item>
                <el-descriptions-item label="店铺id">{{ item.mall_id }}</el-descriptions-item>
                <el-descriptions-item label="提交时间">{{ item.time }}</el-descriptions-item>
                <el-descriptions-item label="所描述">{{ item.info }}</el-descriptions-item>
            </el-descriptions>
        </el-card>
        <div style="display: flex; justify-content: center; margin-top: 20px;">
            <el-pagination
                :page-size="3"
                layout="prev, pager, next"
                :total="total"
                @current-change="getCommodityAudit"
            />
        </div>
    </div>

</template>
<script setup lang="ts">
    import {ref,onMounted} from 'vue'
    import axios from 'axios'
    import { Search } from '@element-plus/icons-vue'
    import { ElMessage } from 'element-plus'

    defineOptions({name:'CommodityAudit',
                    components:{
                        Search
                    }
                })

    const Axios = axios.create({
        baseURL: 'http://127.0.0.1:8000/api',
    })

    interface CommodityAuditList {
        shopping_id: number
        name: string
        mall_id: number
        time: string
        info: string
    }
    const commodity_audit_list = ref<CommodityAuditList[]>([])
    const token = localStorage.getItem('admin_access_token')
    const total = ref(0)
    const select = ref('')
    async function getCommodityAudit(page: number) {
        console.log(select.value)
        if (select.value) {
            const res = await Axios.get('/manage_get_commoidt_apply',{
                params:{
                    select_data:select.value,
                    page:page
                },
                headers:{
                    'access-token': token
                }
            })
            if (res.status == 200) {
                if (res.data.current) {
                    commodity_audit_list.value = res.data.commodity_list
                    total.value = res.data.page
                    console.log(commodity_audit_list.value)
                } else {
                    ElMessage.warning(res.data.msg || '获取数据失败');
                    commodity_audit_list.value = []
                    total.value = 0
                }
            }
        } else {
            const res = await Axios.get('/manage_get_commoidt_apply',{
                params:{
                    page:page
                },
                headers:{
                    'access-token': token
                }
            })
            if (res.status == 200) {
                if (res.data.current) {
                    commodity_audit_list.value = res.data.commodity_list
                    total.value = res.data.page
                    console.log(commodity_audit_list.value)
                } else {
                    ElMessage.warning(res.data.msg || '获取数据失败');
                    commodity_audit_list.value = []
                    total.value = 0
                }
            }
        }

    }
onMounted(async () => {
    await getCommodityAudit(1)
})
</script>
<style scoped>
    :deep(.el-input__wrapper) {
        border-radius: 20px;
    }
    
    .glow-card {
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        margin-bottom: 25px;
        margin-left: 10px;
        margin-right: 10px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08), 0 1px 4px rgba(0, 0, 0, 0.04);
        border: 1px solid rgba(64, 158, 255, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    .glow-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, 
            rgba(64, 158, 255, 0) 0%, 
            rgba(64, 158, 255, 0.5) 50%, 
            rgba(64, 158, 255, 0) 100%);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    
    .glow-card:hover {
        box-shadow: 
            0 8px 24px rgba(64, 158, 255, 0.25),
            0 4px 12px rgba(64, 158, 255, 0.15),
            0 0 0 1px rgba(64, 158, 255, 0.2);
        transform: translateY(-4px) scale(1.01);
        border-color: rgba(64, 158, 255, 0.3);
    }
    
    .glow-card:hover::before {
        opacity: 1;
    }
</style>
