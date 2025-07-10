<template>
  <el-container class="flex flex-col min-h-screen">
    <!-- 导航栏 -->
    <el-header class="bg-white shadow-md">
      <AppNavigation />
    </el-header>
    
    <!-- 内容区 -->
    <el-main class="flex-grow bg-gray-50 py-8 px-4">
      <div class="max-w-3xl mx-auto bg-white rounded-xl shadow-md p-6 md:p-8 transform transition-all duration-300 hover:shadow-lg">
        <div class="text-center mb-8">
          <div class="hrad">
            <h2 class="text-[clamp(1.5rem,3vw,2rem)] font-bold text-gray-800 mb-2">申请成为卖家</h2>
            <el-button v-if="reject_select" @click="reject_content_examin" type="danger" circle><h3>!</h3></el-button>
          </div>
          <p class="text-gray-600">请填写以下信息以申请成为卖家，我们将在3个工作日内审核您的申请</p>
        </div>
        
        <!-- 申请表单 -->
        <el-form 
          ref="applyForm" 
          :model="formData" 
          :rules="rules" 
          label-width="120px" 
          class="space-y-6"
        >
          <el-form-item label="姓名" prop="name">
            <el-input 
              v-model="formData.name" 
              placeholder="请输入您的姓名" 
              class="w-full"
            ></el-input>
          </el-form-item>
          
          <el-form-item label="联系方式" prop="contact">
            <el-input 
              v-model="formData.contact" 
              placeholder="请输入您的手机号码" 
              class="w-full"
            ></el-input>
          </el-form-item>
          
          <el-form-item label="店铺名称" prop="storeName">
            <el-input 
              v-model="formData.storeName" 
              placeholder="请输入店铺名称" 
              class="w-full"
            ></el-input>
          </el-form-item>
          
          <el-form-item label="店铺描述" prop="storeDescription">
            <el-input 
              type="textarea" 
              v-model="formData.storeDescription" 
              placeholder="请简要描述您的店铺和主营商品" 
              class="w-full"
              :rows="4"
            ></el-input>
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="primary" 
              :loading="submitting" 
              @click="submitApplication"
              class="w-full bg-primary text-white hover:bg-blue-600 transition-colors"
            >
              {{ submitting ? '提交中...' : '提交申请' }}
            </el-button>
          </el-form-item>
        </el-form>
        

    </div>
    <el-drawer v-model="drawer" title="驳回理由" :with-header="true" width="35%" :before-close="handleClose">
      <div class="reject-reason-container">
        <div class="reject-icon">
          <el-icon class="warning-icon"><WarningFilled /></el-icon>
        </div>
        <div class="reject-content">
          <p class="reject-text">{{ reject_reason || '暂无驳回理由' }}</p>
        </div>
        <div class="reject-footer">
          <el-button type="primary" @click="drawer = false" class="w-full">我知道了</el-button>
        </div>
      </div>
    </el-drawer>
    </el-main>
    
    <!-- 页尾 -->
    <el-footer class="footer-content">
        <p>版权所有 © [小白的商城]，保留所有权利。</p>
    </el-footer>
  </el-container>
</template>

<script>
import AppNavigation from '@/moon/navigation.vue';
import { ElMessage, ElIcon } from 'element-plus';
import { WarningFilled } from '@element-plus/icons-vue';
import router from '@/router';
import axios from 'axios';

export default {
  name: "ApplySeller",
  data() {
    
    return {
      Axios: axios.create({
        baseURL:'http://127.0.0.1:8000/api'
      }),
      reject_select:false,
      reject_reason:'',
      // 抽屉
      drawer:false,
      // 表单数据
      formData: {
        name: '',
        contact: '',
        storeName: '',
        storeDescription: '',
        token : localStorage.getItem('access_token')
      },
      rules: {
        name: [
          { required: true, message: '请输入您的姓名', trigger: 'blur' },
          { min: 2, message: '姓名长度至少为2个字符', trigger: 'blur' }
        ],
        contact: [
          { required: true, message: '请输入您的联系方式', trigger: 'blur' },
          { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
        ],
        storeName: [
          { required: true, message: '请输入店铺名称', trigger: 'blur' },
          { min: 3, message: '店铺名称长度至少为3个字符', trigger: 'blur' }
        ],
        storeDescription: [
          { required: true, message: '请输入店铺描述', trigger: 'blur' },
          { min: 10, message: '店铺描述至少需要10个字符', trigger: 'blur' }
        ]
      },
      submitting: false,
      showResult: false,
      resultType: 'success',
    }
  },

  mounted(){
  const formdata = new FormData()
  formdata.append('token', this.formData.token);
  // 获取申请卖家内容
    this.Axios.post('/get_apply_seller_content',formdata)
    .then(ref =>{
      console.log(ref.data);
      
      if (ref.status == 200 && ref.data.current) {
        this.formData.name = ref.data.name || '';
        this.formData.contact = ref.data.phone || '';
        this.formData.storeName = ref.data.mall_name || '';
        this.formData.storeDescription = ref.data.mall_describe || '';
        if (ref.data.reject_cause){
          this.drawer = true;
          this.reject_select = true
          this.reject_reason = ref.data.reject_cause
        }
      }
      console.log(ref.data);
    })
  },
  components: {
    AppNavigation
  },
  methods: {
      async submitApplication() {
        try {
            // 先进行表单验证
            const valid = await this.$refs.applyForm.validate();
            if (!valid) {
                ElMessage.warning('请完善表单信息后再提交');
                return;
            }

            const formdata = new FormData();
            formdata.append('token', this.formData.token);
            formdata.append('name', this.formData.name);
            formdata.append('phone', this.formData.contact);
            formdata.append('mall_name', this.formData.storeName);
            formdata.append('mall_describe', this.formData.storeDescription);

            const response = await this.Axios.post('/apply_seller', formdata);
            
            if (response.status === 200) {
                if (response.data.current) {
                    ElMessage.success(response.data.msg);
                    router.push('/personal_center')
                } else {
                    ElMessage.error(response.data.msg);
                }
            }
            this.resultType = 'success';
        } catch (error) {
            console.error('提交失败:', error);
            ElMessage.error('请将所有内容填写完毕');
        }
    },
    //查看驳回内容
    reject_content_examin(){
      this.drawer = true;
    }

  }
}
</script>

<style scoped>

.hrad{
display: flex;
justify-content: space-between;
align-items: center;
width: 100%;
}
.el-button[type='danger'] {
  margin-left: auto;
}
/* 驳回理由抽屉样式 */
.reject-reason-container {
  padding: 24px;
  display: flex;
  flex-direction: column;
  min-height: 200px;
}
.reject-icon {
  text-align: center;
  margin-bottom: 20px;
}
.warning-icon {
  font-size: 48px;
  color: #f59e0b;
  animation: pulse 2s infinite;
}
.reject-content {
  flex: 1;
  padding: 16px;
  background-color: #fffbeb;
  border-radius: 8px;
  border: 1px solid #fde68a;
  margin-bottom: 20px;
}
.reject-text {
  color: #92400e;
  line-height: 1.6;
  white-space: pre-wrap;
}
.reject-footer {
  width: 100%;
}
/* 动画效果 */
@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}
/* 页脚样式 */
.footer-content {
  text-align: center;
  color: darkgray;
}

/* 自定义工具类 */
@layer utilities {
  .content-auto {
    content-visibility: auto;
  }
  .bg-primary {
    background-color: #409eff;
  }
}

/* 全局样式 */
* {
  box-sizing: border-box;
}

/* 表单元素样式优化 */
.el-input__inner {
  border-radius: 0.5rem;
  border-color: #d1d5db;
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  transition: all 0.2s;
}
.el-input__inner:focus {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.2);
  outline: none;
}

.el-form-item__label {
  color: #374151; /* text-gray-700 */
  font-weight: 500; /* font-medium */
}

.el-form-item__error {
  color: #ef4444; /* text-red-500 */
  font-size: 0.875rem; /* text-sm */
  margin-top: 0.25rem; /* mt-1 */
}

/* 提示框样式 */
.el-alert {
  border-radius: 0.5rem; /* rounded-lg */
  padding: 1rem; /* p-4 */
  transition: all 0.3s;
}

.el-alert--success {
  background-color: #f0fdf4; /* bg-green-50 */
  border: 1px solid #bbf7d0; /* border-green-200 */
  color: #15803d; /* text-green-700 */
}

.el-alert--error {
  background-color: #fef2f2; /* bg-red-50 */
  border: 1px solid #fecaca; /* border-red-200 */
  color: #b91c1c; /* text-red-700 */
}

/* 响应式调整 */
@media (max-width: 640px) {
  .el-form-item__label {
    font-size: 0.875rem; /* text-sm */
  }
}
</style>