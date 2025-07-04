<template>
  <div class="user-profile-container">
    <!-- 头像区域 -->
    <div class="avatar-section">
      <el-avatar :size="100" :src="circleUrl"/>
    </div>
    
    <!-- 个人信息列表 -->
    <div class="info-section">
      <ul class="user-info-list">
        <li v-for="(item, index) in personalDetails" :key="index" class="info-item">
          <span class="info-label">{{ item.type }}</span>
          <span class="info-value">{{ item.text }}</span>
        </li>
      </ul>
    </div>
    
  </div>
  <div class="info-section">
    <el-button size="large" style="width: 200px;" @click="skip" round>修改信息<el-icon><Edit /></el-icon></el-button>
  </div>
  
</template>

<script>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import router from '@/router'
import { ElMessage } from 'element-plus';

export default {
  name: 'CenterIndex',
  setup() {
    const circleUrl = ref('https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png')
    
    const personalDetails = ref([
      { type: '昵称', text: '***' },
      { type: '性别', text: '未知' },
      { type: '年龄', text: '*' },
    ]);
    
    const fetchUserInfo = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          ElMessage.error('未登录，请先登录');
          return;
        }
        
        const formData = new FormData();
        formData.append('token', token);
        
        const url = 'http://127.0.0.1:8000/api';
        const response = await axios.post(url + '/userinfo', formData);
        
        if (response.status === 200) {
          if (response.data.current === true) {
            console.log('用户信息:', response.data.data);
            updateUserInfo(response.data.data,);
          } else {
            ElMessage.error(response.data.msg);
          }
        } else {
          ElMessage.error('服务器响应异常');
        }
      } catch (error) {
        console.error('获取用户信息失败:', error);
        ElMessage.error('信息获取失败，请稍后重试');
      }
    };
    
    const updateUserInfo = (data) => {
      personalDetails.value[0].text = data[1] || '未设置';
      personalDetails.value[1].text = data[3] || '未知';
      personalDetails.value[2].text = data[2] || '*';
      if (data[4] != null){
        console.log('yes');
        
        circleUrl.value = 'data:image/png;base64,' +data[4]
        
      }
      else{
         circleUrl.value = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'
      }

    };
    
    onMounted(() => {
      fetchUserInfo();
    });
    
    return {
      circleUrl,
      personalDetails
    };
  },

  methods:{
    skip(){
       router.push('/personal_details_change')
    }
  }
}
</script>

<style scoped>
.user-profile-container {
  padding: 20px;
  border-radius: 8px;
  max-width: 400px;
  margin: 0 auto;
}

.avatar-section {
  text-align: center;
  margin-bottom: 20px;
}

.info-section {
  padding: 15px;
  border-radius: 6px;
}

.user-info-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.info-item {
  display: flex;
  padding: 10px 0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  width: 80px;
  font-weight: 500;
}

.info-value {
  flex: 1;
}

</style>    