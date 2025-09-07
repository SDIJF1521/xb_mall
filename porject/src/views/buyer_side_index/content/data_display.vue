<template>
    <div>
        <el-row :gutter="20" class="mb-4">
            <el-col v-for="item in data" :key="item.name" :xs="24" :sm="12" :md="6" class="text-center">
                <el-statistic :title="item.name" :value="item.value" />
            </el-col>
        </el-row>
        <el-card>
            <div class="chart-container">
                <div ref="pieChart" style="height: 300px;"></div>
            </div>
        </el-card>
    </div>
</template>

<script setup lang="ts">
import axios from 'axios'
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const Axios = axios.create({
    baseURL:'http://127.0.0.1:8000/api',
    timeout:10000,
})

const pieChart = ref<HTMLElement>()

defineOptions({
    name:'DataDisplay',
})

const data = ref([
    {name:'商品总数',value:268500},
    {name:'订单总数',value:12345},
    {name:'用户总数',value:10000},
    {name:'销售额',value:1000000},
])

let chartInstance: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null
let cleanupFunctions: (() => void)[] = []

const initChart = () => {
    if (!pieChart.value || chartInstance) return

    chartInstance = echarts.init(pieChart.value, null, {
        renderer: 'canvas',
        devicePixelRatio: window.devicePixelRatio || 1
    })

    const option = {
        title: {
            text: '交易与库存比例分析',
            left: 'center',
            textStyle: {
                fontSize: 18,
                fontWeight: 'bold'
            }
        },
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            top: 'middle',
            data: ['已完成交易', '库存商品', '处理中交易', '已售商品']
        },
        series: [
            {
                name: '交易库存',
                type: 'pie',
                radius: ['30%', '50%'],
                center: ['50%', '50%'],
                avoidLabelOverlap: false,
                itemStyle: {
                    borderRadius: 10,
                    borderColor: '#fff',
                    borderWidth: 2
                },
                label: {
                    show: false,
                    position: 'center'
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: '20',
                        fontWeight: 'bold'
                    }
                },
                labelLine: {
                    show: false
                },
                data: [
                    { value: 1048, name: '已完成交易', itemStyle: { color: '#5470c6' } },
                    { value: 735, name: '库存商品', itemStyle: { color: '#91cc75' } },
                    { value: 580, name: '处理中交易', itemStyle: { color: '#fac858' } },
                    { value: 484, name: '已售商品', itemStyle: { color: '#ee6666' } }
                ]
            }
        ]
    }

    chartInstance.setOption(option)

    // 使用 ResizeObserver 监听容器大小变化
    if (typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver(() => {
            chartInstance?.resize()
        })
        resizeObserver.observe(pieChart.value)
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

// 组件卸载时清理
onUnmounted(() => {
    cleanupFunctions.forEach(cleanup => cleanup())
    cleanupFunctions = []
})
</script>

<style scoped>
.card{
    display: flex;
}

.chart-container {
    padding: 10px;
    border-radius: 8px;
}
</style>