<template>
  <div class="chart-container">
    <div ref="chartRef"  class="chart"></div>
  </div>
</template>
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { useRoute } from 'vue-router'
import axios from 'axios'
const Axios = axios.create({
    baseURL: "http://127.0.0.1:8000/api",
    headers: {
        'Access-Token': localStorage.getItem('buyer_access_token') || ''
    }
})

const route = useRoute().params
const id = ref(route.id)
const chartRef = ref<HTMLElement>()

interface RoleData {
  role_id: number
  role_name: string
  user_count: number
}

interface ApiResponse {
  code: number
  msg: string
  data: RoleData[]
  current: boolean
}

const role_list = ref<string[]>([])
const chart_data = ref<any[]>([])


const getRoleRatio = async () => {
    try {
      const res = await Axios.get<ApiResponse>('/buyer_role_ratio',{
        params: {
            stroe_id: id.value
        }
      })

      if (res.status === 200 && res.data.code === 200 && res.data.current){
        console.log('Backend response:', res.data);

        // Process the data for the chart
        const roles: string[] = []
        const chartItems: any[] = []

        // Define colors for different roles
        const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de']

        res.data.data.forEach((item, index) => {
          roles.push(item.role_name)
          chartItems.push({
            value: item.user_count,
            name: item.role_name,
            itemStyle: {
              color: colors[index % colors.length]
            }
          })
        })

        role_list.value = roles
        chart_data.value = chartItems
      }
    } catch (error) {
        console.log('Error fetching role ratio:', error)
    }
}


onMounted(async () => {
    await getRoleRatio()
    if (chartRef.value) {
        const myChart = echarts.init(chartRef.value)
        myChart.setOption({
            title: {
                text: '用户角色比例',
                left: 'center',
                top: '10px',
                textStyle: {
                    fontSize: 18,
                    fontWeight: 'bold',
                    color: '#333'
                }
            },
            tooltip: {
                trigger: 'item',
                formatter: '{a} <br/>{b}: {c} ({d}%)',
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: '#ddd',
                textStyle: {
                    color: '#333'
                }
            },
            legend: {
                orient: 'horizontal',
                left: 'center',
                top: '40px',
                data: role_list.value,
                textStyle: {
                    fontSize: 12,
                    color: '#666'
                }
            },
            grid: {
                top: '80px',
                left: '10%',
                right: '10%',
                bottom: '10%',
                containLabel: true
            },
            series: [
                {
                    name: '用户角色',
                    type: 'pie',
                    radius: ['35%', '65%'],
                    center: ['50%', '55%'],
                    avoidLabelOverlap: false,
                    itemStyle: {
                        borderColor: '#fff',
                        borderWidth: 2
                    },
                    label: {
                        show: true,
                        formatter: '{b}: {d}%',
                        fontSize: 12,
                        color: '#333'
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: '14',
                            fontWeight: 'bold'
                        },
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    },
                    labelLine: {
                        show: true,
                        length: 10,
                        length2: 10
                    },
                    data: chart_data.value
                }
            ]
        });
    }
})
</script>

<style scoped>
.chart-container {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    min-height: 500px;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 20px;
    box-sizing: border-box;
}

.chart {
    width: 700px;
    height: 500px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    padding: 20px;
    box-sizing: border-box;
}

@media (max-width: 768px) {
    .chart {
        width: 95%;
        height: 400px;
    }
}
</style>
