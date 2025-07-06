<template>
  <div class="merchant-client-ratio-container">
    <h3 class="chart-title">用户与卖家比例</h3>
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue';
import * as echarts from 'echarts';
import type { ECharts } from 'echarts';
import axios from 'axios';

defineOptions({
  name: 'MerchantClientRatio'
})

const chartRef = ref<HTMLDivElement | null>(null);
let chartInstance: ECharts | null = null;
let intervalId: number | null = null;
const ratioData = ref([
  { name: '用户', value: 0 },
  { name: '卖家', value: 0 }
]);

// 创建Axios实例
const api = axios.create({ baseURL: 'http://127.0.0.1:8000/api' });

// 获取数据函数
const fetchData = async () => {
  try {
    const token = localStorage.getItem('admin_access_token') || '';
    const formdata = new FormData();
    formdata.append('token', token);
    
    // 获取用户列表
    const userResponse = await api.post('/user_list', formdata);
    const userCount = userResponse.data.user_list?.length || 0;
    
    // 获取卖家列表
    const merchantResponse = await api.post('/number_merchants', formdata);
    const merchantCount = merchantResponse.data.merchant_list?.length || 0;
    
    // 更新数据
    ratioData.value = [
      { name: '用户', value: userCount },
      { name: '卖家', value: merchantCount }
    ];
    
    // 更新图表
    updateChart();
  } catch (error) {
    console.error('获取数据失败:', error);
  }
};

// 图表渐变色配置
const chartColors = [
  new echarts.graphic.LinearGradient(0, 0, 1, 0, [
    { offset: 0, color: '#409EFF' },
    { offset: 1, color: '#83bff6' }
  ]),
  new echarts.graphic.LinearGradient(0, 0, 1, 0, [
    { offset: 0, color: '#67C23A' },
    { offset: 1, color: '#b3e19d' }
  ])
];

// 单独提取图表更新逻辑
const updateChart = () => {
  if (!chartInstance) return;
  
  chartInstance.setOption({
    series: [{
      data: ratioData.value // 这里必须使用 .value 获取实际数据
    }]
  });
};

onMounted(() => {
  if (chartRef.value) {
    // 初始化图表实例
    chartInstance = echarts.init(chartRef.value);
    
    // 图表配置 - 关键修复：使用 ratioData.value 而不是 ratioData
    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: <b>{c}</b> ({d}%)'
      },
      legend: {
        orient: 'horizontal',
        bottom: 0,
        textStyle: {
          fontSize: 14,
          color: '#606266'
        },
        itemWidth: 14,
        itemHeight: 14,
        itemGap: 20,
        padding: [10, 0]
      },
      series: [
        {
          name: '用户类型',
          type: 'pie',
          radius: ['40%', '70%'],
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
          animation: true,
          animationDuration: 1000,
          animationEasing: 'cubicInOut',
          animationDurationUpdate: 800,
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            scale: true,
            label: {
              show: true,
              fontSize: 24,
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: ratioData.value, // 修复：使用 .value 获取实际数组
          color: chartColors
        }
      ]
    };

    // 设置图表配置
    chartInstance.setOption(option);
    
    // 立即获取一次数据
    fetchData();
    
    // 设置定时器，每30秒获取一次数据
    intervalId = window.setInterval(fetchData, 30000);

    // 响应窗口大小变化
    window.addEventListener('resize', handleResize);
  }
});

// 处理窗口大小变化
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize();
  }
};

// 组件卸载时清理
onUnmounted(() => {
  if (intervalId) {
    window.clearInterval(intervalId);
  }
  window.removeEventListener('resize', handleResize);
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
});
</script>

<style scoped>
.merchant-client-ratio-container {
  border-radius: 8px;
  box-shadow: 0 4px 20px 0 rgba(63, 80, 233, 0.08);
  padding: 20px;
  height: 100%;
  min-height: 300px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.merchant-client-ratio-container:hover {
  box-shadow: 0 8px 30px 0 rgba(63, 80, 233, 0.12);
}

.chart-title {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 500;
  padding-bottom: 12px;
}

.chart-container {
  flex: 1;
  width: 100%;
  min-height: 250px;
}
</style>