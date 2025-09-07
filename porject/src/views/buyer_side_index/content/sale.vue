<template>
    <div class="sale-container">
        <div ref="chartRef" class="sales-chart"></div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
defineOptions({
    name: 'Sale',
})
const chartRef = ref<HTMLElement>()

let chartInstance: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null
let cleanupFunctions: (() => void)[] = []

const initChart = () => {
    if (!chartRef.value || chartInstance) return

    // 创建图表实例
    chartInstance = echarts.init(chartRef.value, null, {
        renderer: 'canvas',
        devicePixelRatio: window.devicePixelRatio || 1
    })

    // 模拟销售数据
    const salesData = [
        { date: '1月', sales: 12000 },
        { date: '2月', sales: 15000 },
        { date: '3月', sales: 18000 },
        { date: '4月', sales: 22000 },
        { date: '5月', sales: 19000 },
        { date: '6月', sales: 25000 },
        { date: '7月', sales: 28000 },
        { date: '8月', sales: 26000 },
        { date: '9月', sales: 30000 },
        { date: '10月', sales: 32000 },
        { date: '11月', sales: 29000 },
        { date: '12月', sales: 35000 }
    ]

    const option = {
        title: {
            text: '销售额趋势图',
            left: 'center',
            textStyle: {
                fontSize: 16,
                fontWeight: 'bold'
            }
        },
        tooltip: {
            trigger: 'axis',
            formatter: '{b}: ¥{c}',
            backgroundColor: 'rgba(50,50,50,0.8)',
            borderColor: '#333',
            borderWidth: 1,
            textStyle: {
                color: '#fff'
            }
        },
        grid: {
            left: '10%',      /* 增加左边距，适配菜单收起 */
            right: '5%',      /* 增加右边距 */
            bottom: '10%',    /* 增加底部间距 */
            top: '15%',       /* 增加顶部间距 */
            containLabel: true
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: salesData.map(item => item.date),
            axisLine: {
                lineStyle: {
                    color: '#ddd'
                }
            },
            axisLabel: {
                color: '#666',
                rotate: 0, /* 标签不旋转 */
                interval: 'auto' /* 自动调整标签间隔 */
            }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                formatter: '¥{value}',
                color: '#666'
            },
            axisLine: {
                lineStyle: {
                    color: '#ddd'
                }
            },
            splitLine: {
                lineStyle: {
                    color: '#f0f0f0'
                }
            }
        },
        series: [{
            name: '销售额',
            type: 'line',
            data: salesData.map(item => item.sales),
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
                color: '#5470c6',
                width: 3
            },
            itemStyle: {
                color: '#5470c6',
                borderColor: '#fff',
                borderWidth: 2
            },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: 'rgba(84, 112, 198, 0.3)' },
                    { offset: 1, color: 'rgba(84, 112, 198, 0.05)' }
                ])
            }
        }]
    }

    chartInstance.setOption(option)

    // 使用 ResizeObserver 监听容器大小变化
    if (typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver(() => {
            chartInstance?.resize()
        })
        resizeObserver.observe(chartRef.value)
        cleanupFunctions.push(() => {
            if (resizeObserver) {
                resizeObserver.disconnect()
                resizeObserver = null
            }
        })
    }

    // 监听窗口大小变化
    const resizeHandler = () => {
        chartInstance?.resize()
    }
    window.addEventListener('resize', resizeHandler)
    cleanupFunctions.push(() => {
        window.removeEventListener('resize', resizeHandler)
    })

    // 监听菜单展开/收起事件
    const menuObserver = new MutationObserver(() => {
        setTimeout(() => {
            chartInstance?.resize()
        }, 300) // 延迟调整，等待动画完成
    })
    
    const sidebar = document.querySelector('.el-aside') || document.querySelector('.sidebar')
    if (sidebar) {
        menuObserver.observe(sidebar, {
            attributes: true,
            attributeFilter: ['style', 'class']
        })
        cleanupFunctions.push(() => {
            menuObserver.disconnect()
        })
    }

    cleanupFunctions.push(() => {
        if (chartInstance) {
            chartInstance.dispose()
            chartInstance = null
        }
    })
}

onMounted(() => {
    initChart()
})

onUnmounted(() => {
    cleanupFunctions.forEach(cleanup => cleanup())
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
    min-width: 0; /* 防止flex子项溢出 */
}

/* 响应式布局优化 */
@media (max-width: 768px) {
    .sales-chart {
        height: 300px;
        min-height: 250px;
    }
}
</style>