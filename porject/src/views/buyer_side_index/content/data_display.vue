<template>
    <div>
        <el-row :gutter="20" class="mb-4">
            <el-col v-for="item in cardList" :key="item.name" :xs="24" :sm="12" :md="6" class="text-center">
                <el-statistic :title="item.name" :value="item.value" />
            </el-col>
        </el-row>
        <el-card>
            <div class="chart-container">
                <div ref="pieChart" class="chart"></div>
            </div>
        </el-card>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

defineOptions({ name: 'DataDisplay' })

const props = defineProps<{
    cards?: { product_count: number; order_count: number; total_sales: number; pending_refund: number }
    pie?: { name: string; value: number }[]
}>()

const pieChart = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null
let cleanupFunctions: (() => void)[] = []
let resizeTimer: number | null = null

const cardList = ref([
    { name: '商品总数', value: 0 },
    { name: '订单总数', value: 0 },
    { name: '销售额', value: 0 },
    { name: '待处理退款', value: 0 },
])

watch(() => props.cards, (v) => {
    cardList.value = [
        { name: '商品总数', value: v?.product_count ?? 0 },
        { name: '订单总数', value: v?.order_count ?? 0 },
        { name: '销售额', value: v?.total_sales ?? 0 },
        { name: '待处理退款', value: v?.pending_refund ?? 0 },
    ]
}, { immediate: true })

const PIE_COLORS: Record<string, string> = {
    '待支付': '#fac858',
    '已支付': '#5470c6',
    '已发货': '#91cc75',
    '已收货': '#73c0de',
    '已关闭': '#909399',
    '已退款': '#ee6666',
    '退款中': '#fc8452',
}

function renderPie(data: { name: string; value: number }[]) {
    if (!pieChart.value) return

    if (!chartInstance) {
        chartInstance = echarts.init(pieChart.value, null, {
            renderer: 'canvas',
            devicePixelRatio: window.devicePixelRatio || 1,
            useDirtyRect: false,
        })
        setupResize()
    }

    if (!data.length) {
        chartInstance.clear()
        chartInstance.setOption({
            title: {
                text: '订单状态分布',
                subtext: '暂无数据',
                left: 'center',
                top: 'center',
                textStyle: { fontSize: 22, fontWeight: 'bold', color: '#303133' },
                subtextStyle: { fontSize: 14, color: '#909399' },
            },
        })
        return
    }

    const seriesData = data.map(d => ({
        value: d.value,
        name: d.name,
        itemStyle: { color: PIE_COLORS[d.name] || undefined },
    }))

    chartInstance.setOption({
        title: {
            text: '订单状态分布',
            left: 'center',
            top: '15px',
            textStyle: { fontSize: 22, fontWeight: 'bold', color: '#303133' },
        },
        tooltip: {
            trigger: 'item',
            formatter: (params: any) =>
                `<div style="font-weight:600;margin-bottom:4px">${params.seriesName}</div>
                 <div style="color:#409EFF;font-size:16px;font-weight:bold;margin:4px 0">
                   ${params.name}: <span style="color:#303133">${params.value}</span>
                 </div>
                 <div style="color:#909399;font-size:13px">占比: <span style="color:#409EFF;font-weight:bold">${params.percent}%</span></div>`,
            backgroundColor: 'rgba(255,255,255,0.98)',
            borderColor: '#409EFF',
            borderWidth: 2,
            padding: [14, 18],
            extraCssText: 'box-shadow:0 4px 20px rgba(64,158,255,0.2);border-radius:8px;',
        },
        legend: {
            orient: 'horizontal',
            left: 'center',
            top: '50px',
            textStyle: { fontSize: 14, color: '#606266', fontWeight: 500 },
            itemWidth: 16, itemHeight: 16, itemGap: 30, icon: 'circle',
        },
        series: [{
            name: '订单状态',
            type: 'pie',
            radius: ['35%', '65%'],
            center: ['50%', '55%'],
            avoidLabelOverlap: false,
            itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
            label: {
                show: true,
                formatter: (p: any) => `${p.name}\n{percent|${p.percent}%}`,
                fontSize: 13, fontWeight: 600, color: '#303133', lineHeight: 20,
                rich: { percent: { fontSize: 16, fontWeight: 'bold', color: '#409EFF', padding: [4, 0, 0, 0] } },
            },
            emphasis: {
                label: { show: true, fontSize: 15, fontWeight: 'bold' },
                itemStyle: { shadowBlur: 15, shadowColor: 'rgba(64,158,255,0.4)' },
            },
            data: seriesData,
        }],
    }, true)
}

watch(() => props.pie, (v) => {
    renderPie(v ?? [])
}, { immediate: true, deep: true })

function setupResize() {
    if (!pieChart.value || !chartInstance) return

    const handleResize = () => {
        if (resizeTimer) clearTimeout(resizeTimer)
        resizeTimer = window.setTimeout(() => {
            chartInstance?.resize({ animation: { duration: 0 } })
        }, 100)
    }

    if (typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver(handleResize)
        resizeObserver.observe(pieChart.value)
        cleanupFunctions.push(() => { resizeObserver?.disconnect(); resizeObserver = null })
    }
    window.addEventListener('resize', handleResize)
    cleanupFunctions.push(() => window.removeEventListener('resize', handleResize))

    const sidebar = document.querySelector('.el-aside') || document.querySelector('.sidebar')
    if (sidebar) {
        const mo = new MutationObserver(handleResize)
        mo.observe(sidebar, { attributes: true, attributeFilter: ['style', 'class'] })
        cleanupFunctions.push(() => mo.disconnect())
    }

    cleanupFunctions.push(() => {
        if (resizeTimer) { clearTimeout(resizeTimer); resizeTimer = null }
        if (chartInstance) { chartInstance.dispose(); chartInstance = null }
    })
}

onUnmounted(() => {
    cleanupFunctions.forEach(fn => fn())
    cleanupFunctions = []
})
</script>

<style scoped>
.chart-container {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    min-height: 400px;
    padding: 20px;
    box-sizing: border-box;
}
.chart {
    width: 100%;
    height: 400px;
    min-height: 400px;
    background: transparent;
    border-radius: 8px;
    transform: translateZ(0);
}
@media (max-width: 768px) {
    .chart { height: 350px; min-height: 350px; }
    .chart-container { min-height: 350px; }
}
</style>
