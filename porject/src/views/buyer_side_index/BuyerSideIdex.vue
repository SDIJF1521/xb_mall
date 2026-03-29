<template>
    <el-container>
        <el-container>
            <BuyerNavigation />
            <el-container>
                <el-header>
                    <BuyerHead/>
                </el-header>
                <el-main>
                    <div class="toolbar">
                        <el-select
                            v-if="isOwner && storeList.length >= 1"
                            v-model="selectedMallId"
                            placeholder="选择店铺"
                            style="width: 200px"
                            @change="onStoreChange"
                        >
                            <el-option
                                v-for="s in storeList"
                                :key="s.id"
                                :label="s.mall_name"
                                :value="s.id"
                            />
                        </el-select>
                        <el-select v-model="period" placeholder="选择时间范围" style="width: 200px" @change="fetchDashboard">
                            <el-option
                                v-for="item in periodOptions"
                                :key="item.value"
                                :label="item.label"
                                :value="item.value"
                            />
                        </el-select>
                        <el-button type="primary" plain :loading="exporting" @click="exportReport">导出营业报表</el-button>
                    </div>
                    <DataDisplay :cards="dashData.cards" :pie="dashData.pie" />
                    <Sale :trend="dashData.trend" />
                    <RecentOrders :list="dashData.recent_orders" />
                </el-main>
            </el-container>
        </el-container>
        <el-footer class="footer-content">版权所有 © [xb商城]，保留所有权利。</el-footer>
    </el-container>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import BuyerNavigation from '@/moon/buyer_navigation.vue'
import DataDisplay from './content/data_display.vue'
import Sale from './content/sale.vue'
import RecentOrders from './content/recent_orders.vue'
import BuyerHead from '@/moon/buyer_head.vue'
import BuyerTheme from '@/moon/buyer_theme'

defineOptions({
    name: 'BuyerSideIdex',
    components: { BuyerNavigation, DataDisplay, Sale, RecentOrders, BuyerHead },
})

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api', timeout: 15000 })

const period = ref('month')
const periodOptions = [
    { value: 'week', label: '最近一周' },
    { value: 'month', label: '最近一个月' },
    { value: 'three_months', label: '最近三个月' },
    { value: 'year', label: '最近一年' },
]

interface DashData {
    cards: { product_count: number; order_count: number; total_sales: number; pending_refund: number } | undefined
    pie: { name: string; value: number }[]
    trend: { date: string; sales: number }[]
    recent_orders: any[]
}

const exporting = ref(false)

const dashData = reactive<DashData>({
    cards: undefined,
    pie: [],
    trend: [],
    recent_orders: [],
})

const isOwner = ref(false)
const storeList = ref<{ id: number; mall_name: string }[]>([])
const selectedMallId = ref<number | null>(null)

function decodeTokenPayload(token: string): Record<string, any> | null {
    try {
        const parts = token.split('.')
        if (parts.length < 2) return null
        const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/')
        return JSON.parse(atob(payload))
    } catch {
        return null
    }
}

async function loadStoreList() {
    const token = localStorage.getItem('buyer_access_token')
    if (!token) return
    const payload = decodeTokenPayload(token)
    if (!payload || String(payload.station) !== '1') return
    isOwner.value = true
    try {
        const form = new FormData()
        form.append('token', token)
        const res = await Axios.post('/get_mall_name', form)
        if (res.data?.mall_name?.length) {
            storeList.value = res.data.mall_name
            selectedMallId.value = storeList.value[0].id
        }
    } catch (e) {
        console.error('加载店铺列表失败', e)
    }
}

function mallParam(): Record<string, any> {
    const p: Record<string, any> = {}
    if (isOwner.value && selectedMallId.value != null) {
        p.mall_id = selectedMallId.value
    }
    return p
}

function onStoreChange() {
    fetchDashboard()
}

async function fetchDashboard() {
    const token = localStorage.getItem('buyer_access_token')
    if (!token) return
    try {
        const res = await Axios.get('/seller/dashboard/summary', {
            params: { period: period.value, ...mallParam() },
            headers: { 'Access-Token': token },
        })
        if (res.data?.success) {
            dashData.cards = res.data.cards
            dashData.pie = res.data.pie || []
            dashData.trend = res.data.trend || []
            dashData.recent_orders = res.data.recent_orders || []
        } else {
            dashData.cards = undefined
            dashData.pie = []
            dashData.trend = []
            dashData.recent_orders = []
        }
    } catch (e) {
        console.error('仪表盘数据加载失败', e)
        dashData.cards = undefined
        dashData.pie = []
        dashData.trend = []
        dashData.recent_orders = []
    }
}

async function exportReport() {
    const token = localStorage.getItem('buyer_access_token')
    if (!token) return
    exporting.value = true
    try {
        const res = await Axios.get('/seller/dashboard/export', {
            params: { period: period.value, ...mallParam() },
            headers: { 'Access-Token': token },
            responseType: 'blob',
        })
        const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8' })
        const disposition = res.headers['content-disposition'] || ''
        let filename = '营业报表.csv'
        const match = disposition.match(/filename\*=UTF-8''(.+)/)
        if (match) filename = decodeURIComponent(match[1])

        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
    } catch (e) {
        console.error('导出失败', e)
    } finally {
        exporting.value = false
    }
}

onMounted(async () => {
    new BuyerTheme().initTheme()
    await loadStoreList()
    fetchDashboard()
})
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
.toolbar {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
    gap: 12px;
}
</style>
