<template>
    <el-container class="business-container">
      <el-header class="business-header">
        <ManagementNavigation />
      </el-header>
      <!-- 内容 -->
      <el-main class="business-main" v-loading="loading">
        <div class="page-title">
          <h1>商家管理</h1>
          <p class="subtitle">管理商家信息和状态</p>
        </div>
        <div class="main">
          <!-- 信息显示区 -->
           <el-descriptions title="商家信息" border class="business-info-card">
            <el-descriptions-item
              :rowspan="2"
              :width="140"
              label="头像"
              align="center"
            >
              <el-image
                class="business-avatar"
                :src="from_data[6]"
              />
            </el-descriptions-item>
            <el-descriptions-item label="用户名">{{from_data[0]}}</el-descriptions-item>

            <el-descriptions-item label="手机号">{{ from_data[1] }}</el-descriptions-item>

            <el-descriptions-item label="商家名称">{{from_data[2]}}</el-descriptions-item>

            <el-descriptions-item label="状态">
              <el-tag v-if="from_data[3] == '1'" size="small" class="status-tag status-normal">正常</el-tag>
              <el-tag v-else type="danger" size="small" class="status-tag status-error">异常</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="店铺数量">{{from_data[4]}}</el-descriptions-item>

            <el-descriptions-item label="店铺描述">{{from_data[5]}}</el-descriptions-item>

          </el-descriptions>
        </div>
        <!-- 操作按钮 -->
        <div class="button-group">
          <el-button type="primary" @click="handleMerchantStatus" class="action-btn freeze-btn">
            <el-icon><Lock /></el-icon>
            {{from_data[3]=='1'?'冻结账户':'解冻账户'}}
          </el-button>
          <el-button type="danger" @click="delete_merchant" class="action-btn delete-btn">
            <el-icon><Delete /></el-icon>
            删除商家
          </el-button>
        </div>
      </el-main>

      <el-footer class="footer-content">版权所有 © [小白的商城]，保留所有权利。</el-footer>
    </el-container>
</template>
<script setup lang="ts">
import { ref,onMounted } from 'vue';
import { useRoute} from 'vue-router';
import { ElMessage } from 'element-plus';
import { Lock, Delete } from '@element-plus/icons-vue';
import axios from 'axios';
import ManagementNavigation from '@/moon/management_navigation.vue'
import router from '@/router'

defineOptions({
    name:'BusinessManagement',
    components:{
        ManagementNavigation
    }
    })

// 路由参数
const route = useRoute();

const from_data = ref(['username','123456','小白','1','0','***','https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'])
const loading = ref(true)

const Axios = axios.create({
    baseURL:'http://127.0.0.1:8000/api',
})

async function requst_info() {
  const from_url_data = new FormData();
  from_url_data.append('token',localStorage.getItem('admin_access_token')||'');
  from_url_data.append('name',String(route.params.id)||'')

  try {
    await Axios.post('/management_mall_info',from_url_data)
    .then(res=>{
      if (res.status == 200){
        if (res.data.current){
          from_data.value[0] = res.data.mall_info[0]
          from_data.value[1] = res.data.mall_info[2]
          from_data.value[2] = res.data.mall_info[1]
          from_data.value[3] = res.data.mall_info[5]
          from_data.value[4] = res.data.mall_info[4]
          from_data.value[5] = res.data.mall_info[3]
          from_data.value[6] = 'data:image/png;base64,' + res.data.mall_info[6]
          console.log(res.data.mall_info);
        }
      }
    })
  } catch (error) {
    console.error('获取商家信息失败:', error);
  } finally {
    loading.value = false;
  }

  console.log(route.params.id);


}

onMounted(async ()=>{
  await requst_info()
})

// 冻结账户
const freeze_merchant = async ()=>{
  const from_url_data = new FormData();
  from_url_data.append('token',localStorage.getItem('admin_access_token')||'');
  from_url_data.append('name',String(route.params.id)||'')

  try {
    await Axios.post('/manage_merchant_freeze',from_url_data)
    .then(async res=>{
      if (res.status == 200){
        if (res.data.success){
          ElMessage.success('冻结成功')
          // 刷新路由以更新页面数据
          await requst_info()
        }
      }
    })
  } catch (error) {
    console.error('冻结商家失败:', error);
  } finally {
    loading.value = false;
  }
}

async function thaw_merchant () {

  const from_url_data = new FormData();
  from_url_data.append('token',localStorage.getItem('admin_access_token')||'');
  from_url_data.append('name',String(route.params.id)||'')

  try {
    await Axios.post('/manage_merchant_unfreeze',from_url_data)
    .then(async res=>{
      if (res.status == 200){
        if (res.data.success){
          ElMessage.success('解冻成功')
          // 刷新路由以更新页面数据
          await requst_info()
        }
      }
    })
  } catch (error) {
    console.error('解冻商家失败:', error);
  } finally {
    loading.value = false;
  }
}

// 处理商家状态切换
const handleMerchantStatus = () => {
  if (from_data.value[3] == '1') {
    freeze_merchant()
  } else {
    thaw_merchant()
  }
}

async function delete_merchant () {
  const commit = new FormData();
  commit.append('token',localStorage.getItem('admin_access_token')||'');
  commit.append('name',String(route.params.id)||'')
  const res = await Axios.delete('/manage_merchant_delete',{
    data:commit
  })

  if (res.status == 200){
    if (res.data.success){
      ElMessage.success('删除成功')
      // 刷新路由以更新页面数据
      router.push('/user_management')
    }else{
      ElMessage.error('删除失败')
    }
  }

}

</script>
<style scoped>
.footer-content {
  text-align: center;
  color: darkgray;
}
.main{
  margin-bottom: 10px;
}

/* 页面标题 */
.page-title {
  text-align: center;
  margin-bottom: 40px;
  animation: fadeInDown 0.8s ease-out;
}


.subtitle {
  color: #a8a8b3;
  font-size: 16px;
  font-weight: 400;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* 动画效果 */
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 主要内容区域动画 */
.main {
  animation: fadeInUp 0.8s ease-out 0.2s both;
}

.button-group {
  animation: fadeInUp 0.8s ease-out 0.4s both;
  position: relative;
}

/* 选中时的发光效果 */
.button-group:hover {
  box-shadow: 0 0 30px rgba(102, 126, 234, 0.3);
  border: 1px solid rgba(102, 126, 234, 0.5);
}

.button-group:focus-within {
  box-shadow: 0 0 40px rgba(102, 126, 234, 0.5),
              0 0 60px rgba(118, 75, 162, 0.3),
              inset 0 0 20px rgba(102, 126, 234, 0.1);
  border: 2px solid rgba(102, 126, 234, 0.8);
  background: rgba(102, 126, 234, 0.05);
  transform: scale(1.02);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .business-main {
    padding: 20px 10px;
  }

  .main-title {
    font-size: 28px;
  }

  .button-group {
    flex-direction: column;
    align-items: center;
    gap: 15px;
  }

  .action-btn {
    width: 100%;
    max-width: 300px;
  }

  .business-avatar {
    width: 80px;
    height: 80px;
  }
}

/* 加载动画 */
:deep(.el-loading-mask) {
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(5px);
}

:deep(.el-loading-spinner .path) {
  stroke: #667eea;
}

:deep(.el-loading-spinner .el-loading-text) {
  color: #667eea;
  font-weight: 600;
}

.button-group {
  display: flex;
  gap: 20px;
  justify-content: center;
  margin-top: 30px;
  padding: 20px;
  background: transparent;
  border-radius: 16px;
  transition: all 0.3s ease;
}

.action-btn {
  min-width: 140px;
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  position: relative;
  overflow: hidden;
}

.action-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.6s;
}

.action-btn:hover::before {
  left: 100%;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
}

.action-btn:active {
  transform: translateY(0);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}

.freeze-btn {
  background: linear-gradient(135deg, #4a69bd 0%, #6a89cc 100%);
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(74, 105, 189, 0.3);
  transition: all 0.3s ease;
}

.freeze-btn:hover {
  background: linear-gradient(135deg, #3c5aa6 0%, #5a7bb8 100%);
  box-shadow: 0 8px 25px rgba(74, 105, 189, 0.4),
              0 0 20px rgba(102, 126, 234, 0.3);
  transform: translateY(-2px) scale(1.02);
}

.freeze-btn:active {
  box-shadow: 0 0 30px rgba(102, 126, 234, 0.5),
              0 0 40px rgba(118, 75, 162, 0.3);
}

.delete-btn {
  background: linear-gradient(135deg, #eb2f06 0%, #e55039 100%);
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(235, 47, 6, 0.3);
  transition: all 0.3s ease;
}

.delete-btn:hover {
  background: linear-gradient(135deg, #d63031 0%, #d74c2c 100%);
  box-shadow: 0 8px 25px rgba(235, 47, 6, 0.4),
              0 0 20px rgba(235, 47, 6, 0.2);
  transform: translateY(-2px) scale(1.02);
}

.action-btn .el-icon {
  font-size: 18px;
  transition: transform 0.3s ease;
}

.action-btn:hover .el-icon {
  transform: scale(1.1);
}

@keyframes pulse {
  0% {
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  }
  50% {
    box-shadow: 0 4px 25px rgba(74, 105, 189, 0.6);
  }
  100% {
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  }
}

.action-btn:focus {
  animation: pulse 2s infinite;
  outline: none;
}
</style>
