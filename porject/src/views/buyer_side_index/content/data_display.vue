<template>
    <div>
        <el-row :gutter="20" class="mb-4">
            <el-col v-for="item in data" :key="item.name" :xs="24" :sm="12" :md="6" class="text-center">
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
let resizeTimer: number | null = null

const initChart = () => {
    if (!pieChart.value || chartInstance) return

    chartInstance = echarts.init(pieChart.value, null, {
        renderer: 'canvas',
        devicePixelRatio: window.devicePixelRatio || 1,
        useDirtyRect: false // 禁用脏矩形优化，避免缩放时出现残留痕迹
    })

    const option = {
        title: {
            text: '交易与库存比例分析',
            left: 'center',
            top: '15px',
            textStyle: {
                fontSize: 22,
                fontWeight: 'bold',
                color: '#303133',
                fontFamily: 'Microsoft YaHei, PingFang SC, Arial, sans-serif',
                letterSpacing: 1,
                textShadowColor: 'rgba(0, 0, 0, 0.1)',
                textShadowBlur: 4,
                textShadowOffsetX: 0,
                textShadowOffsetY: 2
            }
        },
        tooltip: {
            trigger: 'item',
            formatter: (params: any) => {
                return `<div style="font-weight: 600; margin-bottom: 4px;">${params.seriesName}</div>
                        <div style="color: #409EFF; font-size: 16px; font-weight: bold; margin: 4px 0;">
                            ${params.name}: <span style="color: #303133;">${params.value}</span>
                        </div>
                        <div style="color: #909399; font-size: 13px;">占比: <span style="color: #409EFF; font-weight: bold;">${params.percent}%</span></div>`
            },
            backgroundColor: 'rgba(255, 255, 255, 0.98)',
            borderColor: '#409EFF',
            borderWidth: 2,
            padding: [14, 18],
            textStyle: {
                color: '#303133',
                fontSize: 13,
                fontFamily: 'Microsoft YaHei, PingFang SC, Arial, sans-serif'
            },
            extraCssText: 'box-shadow: 0 4px 20px rgba(64, 158, 255, 0.2); border-radius: 8px;'
        },
        legend: {
            orient: 'horizontal',
            left: 'center',
            top: '50px',
            data: ['已完成交易', '库存商品', '处理中交易', '已售商品'],
            textStyle: {
                fontSize: 14,
                color: '#606266',
                fontWeight: 500,
                fontFamily: 'Microsoft YaHei, PingFang SC, Arial, sans-serif'
            },
            itemWidth: 16,
            itemHeight: 16,
            itemGap: 30,
            icon: 'circle',
            itemStyle: {
                borderWidth: 2
            }
        },
            series: [
            {
                name: '交易库存',
                type: 'pie',
                radius: ['35%', '65%'],
                center: ['50%', '55%'],
                avoidLabelOverlap: false,
                itemStyle: {
                    borderRadius: 10,
                    borderColor: '#fff',
                    borderWidth: 2,
                    shadowBlur: 15,
                    shadowOffsetX: 2,
                    shadowOffsetY: 2,
                    shadowColor: 'rgba(0, 0, 0, 0.1)'
                },
                label: {
                    show: true,
                    formatter: (params: any) => {
                        return `${params.name}\n{percent|${params.percent}%}`
                    },
                    fontSize: 13,
                    fontWeight: 600,
                    color: '#303133',
                    fontFamily: 'Microsoft YaHei, PingFang SC, Arial, sans-serif',
                    lineHeight: 20,
                    rich: {
                        percent: {
                            fontSize: 16,
                            fontWeight: 'bold',
                            color: '#409EFF',
                            padding: [4, 0, 0, 0]
                        }
                    }
                },
                labelLine: {
                    show: true,
                    length: 15,
                    length2: 10,
                    lineStyle: {
                        color: '#C0C4CC',
                        width: 2,
                        type: 'solid'
                    },
                    smooth: 0.2
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: 15,
                        fontWeight: 'bold',
                        color: '#303133',
                        fontFamily: 'Microsoft YaHei, PingFang SC, Arial, sans-serif',
                        formatter: (params: any) => {
                            return `${params.name}\n{percent|${params.percent}%}`
                        },
                        lineHeight: 22,
                        rich: {
                            percent: {
                                fontSize: 18,
                                fontWeight: 'bold',
                                color: '#409EFF'
                            }
                        }
                    },
                    labelLine: {
                        lineStyle: {
                            color: '#409EFF',
                            width: 3
                        }
                    },
                    itemStyle: {
                        shadowBlur: 15,
                        shadowOffsetX: 0,
                        shadowOffsetY: 0,
                        shadowColor: 'rgba(64, 158, 255, 0.4)',
                        borderWidth: 3
                    },
                    scale: true,
                    scaleSize: 5
                },
                animation: true,
                animationDuration: 1000,
                animationEasing: 'cubicInOut',
                animationDurationUpdate: 800,
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

    // 优化的 resize 处理函数
    const handleResize = () => {
        if (!chartInstance) return
        
        // 清除防抖定时器
        if (resizeTimer) {
            clearTimeout(resizeTimer)
        }
        
        // 防抖处理，避免频繁调用
        resizeTimer = window.setTimeout(() => {
            if (chartInstance && pieChart.value) {
                // 调用 resize，确保图表正确重绘
                // ECharts 会自动处理 devicePixelRatio
                chartInstance.resize({
                    animation: {
                        duration: 0 // 禁用动画，避免残留痕迹
                    }
                })
            }
        }, 100) // 100ms 防抖延迟
    }

    // 使用 ResizeObserver 监听容器大小变化
    if (typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver(handleResize)
        resizeObserver.observe(pieChart.value)
        cleanupFunctions.push(() => {
            if (resizeObserver) {
                resizeObserver.disconnect()
                resizeObserver = null
            }
        })
    }

    // 监听窗口大小变化和浏览器缩放
    window.addEventListener('resize', handleResize)
    cleanupFunctions.push(() => {
        window.removeEventListener('resize', handleResize)
    })

    // 监听菜单展开/收起事件
    const menuObserver = new MutationObserver(() => {
        handleResize()
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
        if (resizeTimer) {
            clearTimeout(resizeTimer)
            resizeTimer = null
        }
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
    /* 优化 Canvas 渲染，避免缩放痕迹 */
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
    transform: translateZ(0); /* 启用硬件加速 */
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

.chart :deep(canvas) {
    /* 确保 Canvas 正确清除和重绘 */
    display: block;
    max-width: 100%;
    height: auto;
}

@media (max-width: 768px) {
    .chart {
        height: 350px;
        min-height: 350px;
    }
    
    .chart-container {
        min-height: 350px;
    }
}
</style>