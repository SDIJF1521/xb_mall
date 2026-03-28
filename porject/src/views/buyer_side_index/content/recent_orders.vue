<template>
    <el-card class="recent-orders-card">
        <template #header>
            <span class="card-title">最近订单</span>
        </template>
        <el-table :data="list" stripe style="width:100%" empty-text="暂无订单">
            <el-table-column prop="order_no" label="订单号" min-width="180" show-overflow-tooltip />
            <el-table-column label="商品" min-width="200">
                <template #default="{ row }">
                    <span v-for="(it, i) in (row.items as OrderItem[])" :key="i">
                        {{ it.name }} x{{ it.qty }}<span v-if="(i as number) < row.items.length - 1">、</span>
                    </span>
                </template>
            </el-table-column>
            <el-table-column prop="user" label="买家" width="120" />
            <el-table-column label="金额" width="110" align="right">
                <template #default="{ row }">¥{{ row.total_amount.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
                <template #default="{ row }">
                    <el-tag :type="statusType(row.status)" size="small">{{ row.status_text }}</el-tag>
                </template>
            </el-table-column>
            <el-table-column prop="created_at" label="下单时间" width="170" />
        </el-table>
    </el-card>
</template>

<script setup lang="ts">
defineOptions({ name: 'RecentOrders' })

interface OrderItem { name: string; qty: number }
interface RecentOrder {
    order_no: string
    total_amount: number
    status: string
    status_text: string
    created_at: string | null
    user: string
    items: OrderItem[]
}

defineProps<{ list: RecentOrder[] }>()

const statusType = (s: string) => {
    const map: Record<string, string> = {
        pending: 'warning', paid: '', shipped: 'success',
        received: 'success', closed: 'info', refunded: 'danger', refund_pending: 'danger',
    }
    return map[s] ?? ''
}
</script>

<style scoped>
.recent-orders-card { margin-top: 16px; }
.card-title { font-size: 16px; font-weight: 600; }
</style>
