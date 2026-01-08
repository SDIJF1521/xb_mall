<template>
  <el-container class="apply-seller-container">
    <!-- 导航栏 -->
    <el-header class="header-wrapper">
      <AppNavigation />
    </el-header>
    
    <!-- 内容区 -->
    <el-main class="main-content">
      <div class="form-card">
        <!-- 标题区域 -->
        <div class="header-section">
          <div class="title-wrapper">
            <div class="icon-wrapper">
              <el-icon class="title-icon"><Shop /></el-icon>
            </div>
            <h2 class="page-title">申请成为卖家</h2>
            <el-button 
              v-if="reject_select" 
              @click="reject_content_examin" 
              type="danger" 
              circle
              class="reject-btn"
              :icon="WarningFilled"
            />
          </div>
          <p class="page-subtitle">请填写以下信息以申请成为卖家，我们将在3个工作日内审核您的申请</p>
        </div>
        
        <!-- 申请表单 -->
        <el-form 
          ref="applyForm" 
          :model="formData" 
          :rules="rules" 
          label-width="120px" 
          class="apply-form"
        >
          <el-form-item label="姓名" prop="name" class="form-item-custom">
            <el-input 
              v-model="formData.name" 
              placeholder="请输入您的姓名" 
              class="custom-input"
              :prefix-icon="User"
              clearable
            />
          </el-form-item>
          
          <el-form-item label="联系方式" prop="contact" class="form-item-custom">
            <el-input 
              v-model="formData.contact" 
              placeholder="请输入您的手机号码" 
              class="custom-input"
              :prefix-icon="Phone"
              clearable
            />
          </el-form-item>
          
          <el-form-item label="店铺名称" prop="storeName" class="form-item-custom">
            <el-input 
              v-model="formData.storeName" 
              placeholder="请输入店铺名称" 
              class="custom-input"
              :prefix-icon="Shop"
              clearable
            />
          </el-form-item>
          
          <el-form-item label="店铺描述" prop="storeDescription" class="form-item-custom">
            <el-input 
              type="textarea" 
              v-model="formData.storeDescription" 
              placeholder="请简要描述您的店铺和主营商品（至少10个字符）" 
              class="custom-textarea"
              :rows="5"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
          
          <el-form-item class="submit-item">
            <el-button 
              type="primary" 
              :loading="submitting" 
              @click="submitApplication"
              class="submit-btn"
              size="large"
            >
              <el-icon v-if="!submitting" class="mr-2"><Check /></el-icon>
              {{ submitting ? '提交中...' : '提交申请' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 驳回理由抽屉 -->
      <el-drawer 
        v-model="drawer" 
        title="驳回理由" 
        :with-header="true" 
        width="35%" 
        direction="rtl"
        class="reject-drawer"
      >
        <div class="reject-reason-container">
          <div class="reject-icon">
            <el-icon class="warning-icon"><WarningFilled /></el-icon>
          </div>
          <div class="reject-content">
            <p class="reject-text">{{ reject_reason || '暂无驳回理由' }}</p>
          </div>
          <div class="reject-footer">
            <el-button 
              type="primary" 
              @click="drawer = false" 
              class="confirm-btn"
              size="large"
            >
              <el-icon class="mr-2"><CircleCheck /></el-icon>
              我知道了
            </el-button>
          </div>
        </div>
      </el-drawer>
    </el-main>
    
    <!-- 页尾 -->
    <el-footer class="footer-wrapper">
      <p class="footer-text">版权所有 © [小白的商城]，保留所有权利。</p>
    </el-footer>
  </el-container>
</template>

<script>
import AppNavigation from '@/moon/navigation.vue';
import { ElMessage, ElIcon } from 'element-plus';
import { WarningFilled, Shop, User, Phone, Check, CircleCheck } from '@element-plus/icons-vue';
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
/* 容器样式 */
.apply-seller-container {
  min-height: 100vh;
  background: var(--el-bg-color-page);
  display: flex;
  flex-direction: column;
  transition: background-color 0.3s ease;
}

/* 导航栏样式 */
.header-wrapper {
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  padding: 0;
  height: auto !important;
  transition: all 0.3s ease;
}

/* 主内容区 */
.main-content {
  flex: 1;
  padding: 2rem 1rem;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  background: var(--el-bg-color-page);
  transition: background-color 0.3s ease;
}

/* 表单卡片 */
.form-card {
  width: 100%;
  max-width: 800px;
  background: var(--el-bg-color);
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--el-border-color);
  padding: 3rem 2.5rem;
  animation: fadeInUp 0.6s ease-out;
  transition: all 0.3s ease;
}

.form-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

/* 标题区域 */
.header-section {
  text-align: center;
  margin-bottom: 2.5rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--el-border-color);
}

.title-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  position: relative;
}

.icon-wrapper {
  width: 60px;
  height: 60px;
  background: linear-gradient(to right, #7ef0b3, #9c6edd);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(126, 240, 179, 0.3);
  animation: float 3s ease-in-out infinite;
  transition: all 0.3s ease;
}

.dark .icon-wrapper {
  background: linear-gradient(to right, #46e2cb, #742bd9);
  box-shadow: 0 4px 15px rgba(70, 226, 203, 0.3);
}

.title-icon {
  font-size: 28px;
  color: #ffffff;
}

.page-title {
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  font-weight: 600;
  background: linear-gradient(to right, #7ef0b3, #9c6edd);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  margin: 0;
  letter-spacing: -0.5px;
}

.dark .page-title {
  background: linear-gradient(to right, #46e2cb, #742bd9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.reject-btn {
  position: absolute;
  right: 0;
  animation: shake 0.5s ease-in-out infinite;
}

.reject-btn:hover {
  animation: none;
  transform: scale(1.1);
}

.page-subtitle {
  color: var(--el-text-color-regular);
  font-size: 1rem;
  line-height: 1.6;
  margin-top: 0.5rem;
  transition: color 0.3s ease;
}

/* 表单样式 */
.apply-form {
  margin-top: 1.5rem;
}

.form-item-custom {
  margin-bottom: 1.75rem;
}

.form-item-custom :deep(.el-form-item__label) {
  color: var(--el-text-color-primary);
  font-weight: 600;
  font-size: 1rem;
  padding-bottom: 0.5rem;
  transition: color 0.3s ease;
}

.custom-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  transition: all 0.3s ease;
  background-color: var(--el-fill-color-blank);
  border-color: var(--el-border-color);
}

.custom-input :deep(.el-input__wrapper:hover) {
  border-color: var(--el-color-primary-light-7);
}

.custom-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px var(--el-color-primary-light-8);
}

.custom-textarea :deep(.el-textarea__inner) {
  border-radius: 8px;
  transition: all 0.3s ease;
  background-color: var(--el-fill-color-blank);
  border-color: var(--el-border-color);
  font-family: inherit;
  line-height: 1.6;
  color: var(--el-text-color-primary);
}

.custom-textarea :deep(.el-textarea__inner:hover) {
  border-color: var(--el-color-primary-light-7);
}

.custom-textarea :deep(.el-textarea__inner:focus) {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px var(--el-color-primary-light-8);
}

.submit-item {
  margin-top: 2.5rem;
  margin-bottom: 0;
}

.submit-btn {
  width: 100%;
  height: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.submit-btn:hover {
  transform: translateY(-2px);
}

.submit-btn:active {
  transform: translateY(0);
}

/* 驳回理由抽屉样式 */
.reject-drawer :deep(.el-drawer__header) {
  margin-bottom: 0;
  padding: 1.5rem 1.5rem 1rem;
  border-bottom: 1px solid var(--el-border-color);
}

.reject-drawer :deep(.el-drawer__body) {
  background: var(--el-bg-color);
}

.reject-reason-container {
  padding: 2rem;
  display: flex;
  flex-direction: column;
  min-height: 300px;
  align-items: center;
}

.reject-icon {
  text-align: center;
  margin-bottom: 2rem;
}

.warning-icon {
  font-size: 64px;
  color: var(--el-color-warning);
  animation: pulse 2s ease-in-out infinite;
}

.reject-content {
  flex: 1;
  width: 100%;
  padding: 1.5rem;
  background: var(--el-color-warning-light-9);
  border-radius: 12px;
  border: 1px solid var(--el-color-warning-light-7);
  margin-bottom: 2rem;
  transition: all 0.3s ease;
}

.dark .reject-content {
  background: var(--el-color-warning-dark-2);
  border-color: var(--el-color-warning-dark-1);
}

.reject-text {
  color: var(--el-text-color-primary);
  line-height: 1.8;
  white-space: pre-wrap;
  font-size: 1rem;
  margin: 0;
  transition: color 0.3s ease;
}

.reject-footer {
  width: 100%;
}

.confirm-btn {
  width: 100%;
  height: 48px;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.confirm-btn:hover {
  transform: translateY(-2px);
}

/* 页脚样式 */
.footer-wrapper {
  background: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color);
  padding: 1.5rem;
  text-align: center;
  transition: all 0.3s ease;
}

.footer-text {
  color: var(--el-text-color-regular);
  font-size: 0.9rem;
  margin: 0;
  transition: color 0.3s ease;
}

/* 动画效果 */
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

@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.9;
  }
}

@keyframes shake {
  0%, 100% {
    transform: rotate(0deg);
  }
  25% {
    transform: rotate(-5deg);
  }
  75% {
    transform: rotate(5deg);
  }
}

/* 表单错误提示样式 */
.form-item-custom :deep(.el-form-item__error) {
  color: var(--el-color-error);
  font-size: 0.875rem;
  margin-top: 0.5rem;
  padding-left: 0.25rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .form-card {
    padding: 2rem 1.5rem;
    border-radius: 16px;
  }

  .title-wrapper {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .reject-btn {
    position: static;
    margin-left: auto;
  }

  .icon-wrapper {
    width: 50px;
    height: 50px;
  }

  .title-icon {
    font-size: 24px;
  }

  .page-title {
    font-size: 1.75rem;
  }

  .form-item-custom :deep(.el-form-item__label) {
    font-size: 0.9rem;
  }

  .reject-drawer :deep(.el-drawer) {
    width: 90% !important;
  }
}

@media (max-width: 480px) {
  .main-content {
    padding: 1rem 0.5rem;
  }

  .form-card {
    padding: 1.5rem 1rem;
  }

  .header-section {
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
  }

  .page-title {
    font-size: 1.5rem;
  }

  .page-subtitle {
    font-size: 0.9rem;
  }

  .submit-btn {
    height: 48px;
    font-size: 1rem;
  }
}

/* 工具类 */
.mr-2 {
  margin-right: 0.5rem;
}
</style>