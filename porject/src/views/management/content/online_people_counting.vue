<template>
    <el-card style="width: 100%; max-width: 90%; margin: 0 auto" shadow="always">
        <div class="title-container">
            <h4 class="online-title">在线人数</h4>
            <el-icon><UserFilled /></el-icon>
        </div>
        <!-- 添加key属性确保数值变化时触发过渡动画 -->
        <transition name="number-change"><h3 class="online-count" :key="number_people">{{ number_people }}</h3></transition>
    </el-card>
</template>
<script lang="ts">
import { onMounted, onUnmounted, ref, Transition } from 'vue';
import { UserFilled } from '@element-plus/icons-vue';
import axios from 'axios';

export default {
  name: 'ExampleView',
  setup() {
    let intervalId: number | null = null;
    const token = localStorage.getItem('admin_access_token') || '';
    // 定义响应式变量，初始值为 0
    const number_people = ref(0);

    const sendRequest = async () => {
      try {
        await axios.get(`http://127.0.0.1:8000/api/get_online_user_list?token=${token}`)
        .then(ref =>{
            if (ref.status === 200) {
                if (ref.data.current){
                    number_people.value=Object.keys(ref.data.online_users).length;
                }else{
                    number_people.value = 0
                }
            }
        })
        
      } catch (error) {
        console.error('请求失败', error);
      }
    };

    onMounted(() => {
      // 组件挂载后，立即发送第一次请求
      sendRequest();
      // 每隔 30 秒发送一次请求
      intervalId = window.setInterval(sendRequest, 30000);
    });

    onUnmounted(() => {
      // 组件卸载时，清除定时器
      if (intervalId) {
        window.clearInterval(intervalId);
      }
    });

    // 返回响应式变量，确保模板可以访问
    return {
      number_people
    };
  },
};
</script>
<style scoped>
.el-card {
  padding: 22px;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.1), inset 0 -1px 3px rgba(255, 255, 255, 0.5);
}

.title-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.online-title {
  font-size: 1.2rem;
  color: #333;
}

.online-count {
  font-size: 2rem;
  font-weight: bold;
  color: #409EFF;
  text-align: center;
}

/* 数字变化过渡动画 */
.number-change-enter-from, .number-change-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.number-change-enter-active, .number-change-leave-active {
  transition: all 0.5s ease;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .el-card {
    padding: 15px;
  }
  .online-title {
    font-size: 1rem;
  }
  .online-count {
    font-size: 1.8rem;
  }
}

@media (max-width: 480px) {
  .el-card {
    padding: 10px;
  }
  .online-title {
    font-size: 0.9rem;
  }
  .online-count {
    font-size: 1.5rem;
  }
}
</style>