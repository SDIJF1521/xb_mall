<template>
    <div class="sale-container">
        <div ref="chartRef" class="sales-chart"></div>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

defineOptions({ name: 'Sale' })

const props = defineProps<{
    trend?: { date: string; sales: number }[]
}>()

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null
let cleanupFunctions: (() => void)[] = []

function renderChart(data: { date: string; sales: number }[]) {
    if (!chartRef.value) return

    if (!chartInstance) {
        chartInstance = echarts.init(chartRef.value, null, {
            renderer: 'canvas',
            devicePixelRatio: window.devicePixelRatio || 1,
        })
        setupResize()
    }

    if (!data.length) {
        chartInstance.clear()
        chartInstance.setOption({
            title: {
                text: '销售额趋势',
                subtext: '暂无数据',
                left: 'center',
                top: 'center',
                textStyle: { fontSize: 16, fontWeight: 'bold' },
                subtextStyle: { fontSize: 14, color: '#909399' },
            },
        })
        return
    }

    chartInstance.setOption({
        title: {
            text: '销售额趋势',
            left: 'center',
            textStyle: { fontSize: 16, fontWeight: 'bold' },
        },
        tooltip: {
            trigger: 'axis',
            formatter: '{b}: ¥{c}',
            backgroundColor: 'rgba(50,50,50,0.8)',
            borderColor: '#333',
            textStyle: { color: '#fff' },
        },
        grid: { left: '10%', right: '5%', bottom: '10%', top: '15%', containLabel: true },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: data.map(d => d.date),
            axisLine: { lineStyle: { color: '#ddd' } },
            axisLabel: { color: '#666', rotate: data.length > 15 ? 45 : 0, interval: 'auto' },
        },
        yAxis: {
            type: 'value',
            axisLabel: { formatter: '¥{value}', color: '#666' },
            axisLine: { lineStyle: { color: '#ddd' } },
            splitLine: { lineStyle: { color: '#f0f0f0' } },
        },
        series: [{
            name: '销售额',
            type: 'line',
            data: data.map(d => d.sales),
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: { color: '#5470c6', width: 3 },
            itemStyle: { color: '#5470c6', borderColor: '#fff', borderWidth: 2 },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: 'rgba(84,112,198,0.3)' },
                    { offset: 1, color: 'rgba(84,112,198,0.05)' },
                ]),
            },
        }],
    }, true)
}

watch(() => props.trend, (v) => {
    renderChart(v ?? [])
}, { immediate: true, deep: true })

function setupResize() {
    if (!chartRef.value || !chartInstance) return

    const handleResize = () => chartInstance?.resize()

    if (typeof ResizeObserver !== 'undefined') {
        const ro = new ResizeObserver(handleResize)
        ro.observe(chartRef.value)
        cleanupFunctions.push(() => ro.disconnect())
    }
    window.addEventListener('resize', handleResize)
    cleanupFunctions.push(() => window.removeEventListener('resize', handleResize))

    const sidebar = document.querySelector('.el-aside') || document.querySelector('.sidebar')
    if (sidebar) {
        const mo = new MutationObserver(() => setTimeout(handleResize, 300))
        mo.observe(sidebar, { attributes: true, attributeFilter: ['style', 'class'] })
        cleanupFunctions.push(() => mo.disconnect())
    }

    cleanupFunctions.push(() => { chartInstance?.dispose(); chartInstance = null })
}

onUnmounted(() => {
    cleanupFunctions.forEach(fn => fn())
    cleanupFunctions = []
})
</script>

<style scoped>
.sale-container {
    width: 100%;
    max-width: 100%;
    overflow: hidden;
    position: relative;
}
.sales-chart {
    width: 100%;
    height: 400px;
    min-height: 300px;
    background-color: #fff;
    border-radius: 8px;
    min-width: 0;
}
@media (max-width: 768px) {
    .sales-chart { height: 300px; min-height: 250px; }
}
</style>
