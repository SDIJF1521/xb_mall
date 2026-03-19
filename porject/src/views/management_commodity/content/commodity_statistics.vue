<template>
    <div class="statistics-container">
        <div v-if="loading" class="loading-container">
            <el-skeleton :rows="8" animated />
        </div>
        <div v-else>
            <!-- 概览卡片 -->
            <div class="overview-cards">
                <el-card class="stat-card" shadow="hover">
                    <div class="stat-value total">{{ statistics.total }}</div>
                    <div class="stat-label">商品总数</div>
                </el-card>
                <el-card class="stat-card" shadow="hover">
                    <div class="stat-value on-sale">{{ statistics.on_sale }}</div>
                    <div class="stat-label">已上架</div>
                </el-card>
                <el-card class="stat-card" shadow="hover">
                    <div class="stat-value off-shelf">{{ statistics.off_shelf }}</div>
                    <div class="stat-label">已下架</div>
                </el-card>
                <el-card class="stat-card" shadow="hover">
                    <div class="stat-value auditing">{{ statistics.auditing }}</div>
                    <div class="stat-label">审核中</div>
                </el-card>
                <el-card class="stat-card" shadow="hover">
                    <div class="stat-value rejected">{{ statistics.rejected }}</div>
                    <div class="stat-label">已驳回</div>
                </el-card>
                <el-card class="stat-card" shadow="hover">
                    <div class="stat-value violation">{{ statistics.violation }}</div>
                    <div class="stat-label">违规商品</div>
                </el-card>
            </div>

            <!-- 图表区域 -->
            <div class="chart-section">
                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-card shadow="hover" class="chart-card">
                            <template #header>
                                <span class="chart-title">商品状态分布</span>
                            </template>
                            <div ref="statusChartRef" class="chart-box"></div>
                        </el-card>
                    </el-col>
                    <el-col :span="12">
                        <el-card shadow="hover" class="chart-card">
                            <template #header>
                                <span class="chart-title">店铺商品TOP10</span>
                            </template>
                            <div ref="storeChartRef" class="chart-box"></div>
                        </el-card>
                    </el-col>
                </el-row>
                <el-row :gutter="20" style="margin-top: 20px;">
                    <el-col :span="12">
                        <el-card shadow="hover" class="chart-card">
                            <template #header>
                                <span class="chart-title">分类商品分布</span>
                            </template>
                            <div ref="classifyChartRef" class="chart-box"></div>
                        </el-card>
                    </el-col>
                    <el-col :span="12">
                        <el-card shadow="hover" class="chart-card">
                            <template #header>
                                <span class="chart-title">近7天新增商品趋势</span>
                            </template>
                            <div ref="trendChartRef" class="chart-box"></div>
                        </el-card>
                    </el-col>
                </el-row>
            </div>
        </div>
    </div>
</template>
<script setup lang="ts">
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

defineOptions({ name: 'CommodityStatistics' })

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })
const token = localStorage.getItem('admin_access_token')

const loading = ref(true)

const statistics = ref({
    total: 0,
    on_sale: 0,
    off_shelf: 0,
    auditing: 0,
    rejected: 0,
    violation: 0
})

const store_distribution = ref<any[]>([])
const classify_distribution = ref<any[]>([])
const trend = ref<any[]>([])

const statusChartRef = ref<HTMLElement>()
const storeChartRef = ref<HTMLElement>()
const classifyChartRef = ref<HTMLElement>()
const trendChartRef = ref<HTMLElement>()

let statusChart: echarts.ECharts | null = null
let storeChart: echarts.ECharts | null = null
let classifyChart: echarts.ECharts | null = null
let trendChart: echarts.ECharts | null = null

async function getStatistics() {
    loading.value = true
    try {
        const res = await Axios.get('/manage_commodity_statistics', {
            headers: { 'access-token': token }
        })
        if (res.status === 200 && res.data.current) {
            statistics.value = res.data.statistics
            store_distribution.value = res.data.store_distribution || []
            classify_distribution.value = res.data.classify_distribution || []
            trend.value = res.data.trend || []

            loading.value = false
            await nextTick()
            renderCharts()
        } else {
            ElMessage.warning(res.data.msg || '获取统计数据失败')
        }
    } catch (e) {
        ElMessage.error('请求失败')
    } finally {
        loading.value = false
    }
}

function renderCharts() {
    renderStatusChart()
    renderStoreChart()
    renderClassifyChart()
    renderTrendChart()
}

function renderStatusChart() {
    if (!statusChartRef.value) return
    statusChart = echarts.init(statusChartRef.value)
    statusChart.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { bottom: 0, textStyle: { color: '#999' } },
        series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: { borderRadius: 10, borderColor: 'transparent', borderWidth: 2 },
            label: { show: false },
            emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
            data: [
                { value: statistics.value.on_sale, name: '已上架', itemStyle: { color: '#67C23A' } },
                { value: statistics.value.off_shelf, name: '已下架', itemStyle: { color: '#E6A23C' } },
                { value: statistics.value.auditing, name: '审核中', itemStyle: { color: '#909399' } },
                { value: statistics.value.rejected, name: '已驳回', itemStyle: { color: '#F56C6C' } },
                { value: statistics.value.violation, name: '违规', itemStyle: { color: '#ff4757' } },
            ]
        }]
    })
}

function renderStoreChart() {
    if (!storeChartRef.value || store_distribution.value.length === 0) return
    storeChart = echarts.init(storeChartRef.value)
    storeChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: {
            type: 'category',
            data: store_distribution.value.map(i => i.mall_name),
            axisLabel: { rotate: 30, fontSize: 11, color: '#999' }
        },
        yAxis: { type: 'value', axisLabel: { color: '#999' } },
        grid: { left: 50, right: 20, bottom: 60, top: 20 },
        series: [{
            type: 'bar',
            data: store_distribution.value.map(i => i.count),
            itemStyle: {
                borderRadius: [6, 6, 0, 0],
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#409EFF' },
                    { offset: 1, color: '#79bbff' }
                ])
            }
        }]
    })
}

function renderClassifyChart() {
    if (!classifyChartRef.value || classify_distribution.value.length === 0) return
    classifyChart = echarts.init(classifyChartRef.value)
    classifyChart.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { bottom: 0, textStyle: { color: '#999' } },
        series: [{
            type: 'pie',
            radius: '65%',
            data: classify_distribution.value.map(i => ({
                value: i.count,
                name: i.name
            })),
            emphasis: {
                itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.3)' }
            }
        }]
    })
}

function renderTrendChart() {
    if (!trendChartRef.value || trend.value.length === 0) return
    trendChart = echarts.init(trendChartRef.value)
    trendChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: {
            type: 'category',
            data: trend.value.map(i => i.date),
            axisLabel: { color: '#999' }
        },
        yAxis: { type: 'value', minInterval: 1, axisLabel: { color: '#999' } },
        grid: { left: 50, right: 20, bottom: 30, top: 20 },
        series: [{
            type: 'line',
            data: trend.value.map(i => i.count),
            smooth: true,
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: 'rgba(64,158,255,0.3)' },
                    { offset: 1, color: 'rgba(64,158,255,0.02)' }
                ])
            },
            lineStyle: { color: '#409EFF', width: 2 },
            itemStyle: { color: '#409EFF' }
        }]
    })
}

function handleResize() {
    statusChart?.resize()
    storeChart?.resize()
    classifyChart?.resize()
    trendChart?.resize()
}

onMounted(() => {
    getStatistics()
    window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
    window.removeEventListener('resize', handleResize)
    statusChart?.dispose()
    storeChart?.dispose()
    classifyChart?.dispose()
    trendChart?.dispose()
})
</script>
<style scoped>
.statistics-container {
    padding: 10px;
}

.loading-container {
    padding: 40px;
}

.overview-cards {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}

.stat-card {
    text-align: center;
    border-radius: 12px;
    transition: all 0.3s ease;
}

.stat-card:hover {
    transform: translateY(-4px);
}

.stat-value {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 8px;
}

.stat-value.total { color: #409EFF; }
.stat-value.on-sale { color: #67C23A; }
.stat-value.off-shelf { color: #E6A23C; }
.stat-value.auditing { color: #909399; }
.stat-value.rejected { color: #F56C6C; }
.stat-value.violation { color: #ff4757; }

.stat-label {
    font-size: 14px;
    color: var(--el-text-color-secondary);
}

.chart-card {
    border-radius: 12px;
}

.chart-title {
    font-size: 15px;
    font-weight: 500;
}

.chart-box {
    width: 100%;
    height: 320px;
}

@media screen and (max-width: 1200px) {
    .overview-cards {
        grid-template-columns: repeat(3, 1fr);
    }
}

@media screen and (max-width: 768px) {
    .overview-cards {
        grid-template-columns: repeat(2, 1fr);
    }
}
</style>
