<template>
  <div class="personal-details-change-container">
    <el-container class="change-container">
      <el-header class="header-wrapper">
        <AppNavigation/>
      </el-header>
      <el-main class="main-wrapper">
        <div class="form-layout">
          <!-- 页面标题 -->
          <div class="page-header">
            <div class="header-icon-wrapper">
              <el-icon class="header-icon"><Edit /></el-icon>
            </div>
            <h2 class="page-title">修改个人信息</h2>
            <p class="page-subtitle">更新您的个人资料和头像</p>
          </div>

          <!-- 表单卡片 -->
          <div class="form-card">
            <!-- 头像上传区域 -->
            <div class="avatar-section">
              <div class="section-header">
                <el-icon class="section-icon"><Avatar /></el-icon>
                <h3 class="section-title">头像设置</h3>
              </div>
              
              <div class="upload-area">
                <el-upload
                  class="avatar-uploader"
                  drag
                  :auto-upload="false"
                  v-model:file-list="fileList"
                  :limit="1"
                  :disabled="on_upload"
                  :on-change="handleFileChange"
                  accept="image/*"
                >
                  <el-icon class="upload-icon"><UploadFilled /></el-icon>
                  <div class="upload-text">
                    拖拽图片到此处或<em>点击上传</em>
                  </div>
                  <div class="upload-hint">支持 JPG、PNG、GIF 等格式，大小不超过 5MB</div>
                </el-upload>
                
                <!-- 图片预览区域 -->
                <div class="preview-container" v-if="previewImage">
                  <div class="preview-wrapper">
                    <img :src="previewImage" class="preview-image" alt="预览图片">
                    <div class="preview-overlay">
                      <el-button 
                        class="delete-button" 
                        @click="imageDelete" 
                        type="danger"
                        :icon="Delete"
                        circle
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 基本信息区域 -->
            <div class="info-section">
              <div class="section-header">
                <el-icon class="section-icon"><UserFilled /></el-icon>
                <h3 class="section-title">基本信息</h3>
              </div>

              <div class="form-content">
                <el-form :model="formData" label-width="100px" class="info-form">
                  <el-form-item label="昵称" class="form-item-custom">
                    <el-input
                      v-model="name"
                      placeholder="请输入您的昵称"
                      class="custom-input"
                      :prefix-icon="User"
                      clearable
                      maxlength="20"
                      show-word-limit
                    />
                  </el-form-item>

                  <el-form-item label="性别" class="form-item-custom">
                    <el-select 
                      v-model="value" 
                      placeholder="请选择性别" 
                      class="custom-select"
                      :prefix-icon="UserFilled"
                    >
                      <el-option
                        v-for="item in options"
                        :key="item.value"
                        :label="item.label"
                        :value="item.value"
                        :disabled="item.disabled"
                      />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item label="年龄" class="form-item-custom">
                    <el-input-number
                      v-model="num"
                      :min="1"
                      :max="300"
                      controls-position="right"
                      class="custom-number-input"
                      placeholder="请输入年龄"
                    />
                  </el-form-item>
                </el-form>
              </div>
            </div>

            <!-- 提交按钮 -->
            <div class="submit-section">
              <el-button 
                type="primary" 
                @click="SubmitEvent" 
                class="submit-btn"
                :icon="Check"
                size="large"
                :loading="submitting"
              >
                {{ submitting ? '提交中...' : '保存修改' }}
              </el-button>
              <el-button 
                @click="goBack" 
                class="cancel-btn"
                :icon="Close"
                size="large"
              >
                取消
              </el-button>
            </div>
          </div>
        </div>
      </el-main>
      <el-footer class="footer-wrapper">
        <p class="footer-text">版权所有 © [小白的商城]，保留所有权利。</p>
      </el-footer>
    </el-container>
  </div>
</template>

<script>
import AppNavigation from '@/moon/navigation.vue'
import axios from 'axios';
import { ElMessage } from 'element-plus';
import router from '@/router';
import { 
  Edit, 
  Avatar, 
  UserFilled, 
  UploadFilled, 
  Delete, 
  User, 
  Check, 
  Close 
} from '@element-plus/icons-vue';

export default {
  name: "PersonalDetailsChange",
  data() {
    return {
      fileList: [],
      on_upload: false,
      previewImage: '',
      value: '未知',
      num: 1,
      name: '',
      submitting: false,
      formData: {
        name: '',
        sex: '未知',
        age: 1
      },
      options: [
        { value: '男', label: '男' },
        { value: '女', label: '女' },
        { value: '未知', label: '未知' }
      ],
      Axios: axios.create({
        baseURL: 'http://127.0.0.1:8000/api'
      })
    }
  },


// 进入网页后立即执行方法
mounted() {
  const formdata = new FormData()
  const token = localStorage.getItem('access_token')
  formdata.append('token', token)
  this.Axios.post('/userinfo', formdata)
    .then(ref => {
      if (ref.status == 200 && ref.data.current) {
        this.value = ref.data.data[3] || '未知'
        this.num = ref.data.data[2] || 1
        this.name = ref.data.data[1] || ''
      }
    })
},
  watch: {
    fileList: {
      deep: true,
      handler(newVal) {
        console.log('文件列表更新:', newVal);
        if (newVal.length == 1){
          const imageExtensions = ['jpg','png','gif','bmp','webp','svg','jpeg']
          const file = newVal[0];
          const filename = file?.name || '';
          const ext = filename.split('.').pop()?.toLowerCase();
          if (!(ext && imageExtensions.includes(ext))){
            ElMessage.error('文件必须是图片');
            this.fileList = [];
            this.on_upload = false;
          }else{
            this.on_upload = true;
          }
          
        }else{
          this.on_upload = false;
        }
        this.updatePreview(); // 监听文件列表变化更新预览
      }
    }
  },
  components: {
    AppNavigation,
    Edit,
    Avatar,
    UserFilled,
    UploadFilled,
    Delete,
    User,
    Check,
    Close
  },
  methods: {
    // 处理文件变化
    handleFileChange(file, fileList) {
      console.log('选择的文件:', file);
      this.updatePreview();
    },
    
    // 更新预览图片
    updatePreview() {
      if (this.fileList.length > 0) {
        const file = this.fileList[0];
        // 优先使用已上传的URL，否则使用本地文件URL
        this.previewImage = file.url || URL.createObjectURL(file.raw);
      } else {
        this.previewImage = '';
      }
    },
    // 删除图片
    imageDelete(){
       this.fileList = [];
    },
    async SubmitEvent(){
      this.submitting = true;
      const token = localStorage.getItem('access_token');
      
      try {
        // 上传头像
        if (this.previewImage != '') {
          try {
            const response = await fetch(this.previewImage);
            const blob = await response.blob();
            const formdata = new FormData();
            formdata.append('file', blob, this.previewImage);
            formdata.append('token', token);
            
            const uploadResult = await this.Axios({
              method: 'patch',
              url: '/uploading_profile_photo',
              data: formdata
            });
            
            if (uploadResult.status == 200) {
              if (uploadResult.data.current) {
                ElMessage.success(uploadResult.data.msg);
                this.previewImage = '';
              } else {
                ElMessage.error(uploadResult.data.msg);
              }
            } else {
              ElMessage.error('图片上传失败');
            }
          } catch (error) {
            ElMessage.error('图片上传失败');
            console.error('图片上传错误:', error);
          }
        }
        
        // 更新用户信息
        const formdata = new FormData();
        formdata.append('nickname', this.name);
        formdata.append('age', this.num);
        formdata.append('sex', this.value);
        formdata.append('token', token);
        
        const result = await this.Axios({
          method: 'patch',
          url: '/user_data_amend',
          data: formdata
        });
        
        if (result.status == 200) {
          if (result.data.current) {
            ElMessage.success(result.data.msg);
            setTimeout(() => {
              router.push('/personal_center');
            }, 1000);
          } else {
            ElMessage.error(result.data.msg);
          }
        } else {
          ElMessage.error('请求错误');
        }
      } catch (error) {
        ElMessage.error('操作失败，请稍后重试');
        console.error('提交错误:', error);
      } finally {
        this.submitting = false;
      }
    },
    goBack() {
      router.push('/personal_center');
    }
  }
}
</script>

<style scoped>
/* 容器样式 */
.personal-details-change-container {
  min-height: 100vh;
  background: var(--el-bg-color-page);
  transition: background-color 0.3s ease;
}

.change-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 头部样式 */
.header-wrapper {
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  padding: 0;
  transition: all 0.3s ease;
}

/* 主内容区 */
.main-wrapper {
  flex: 1;
  padding: 2rem 1rem;
  background: var(--el-bg-color-page);
  transition: background-color 0.3s ease;
}

.form-layout {
  max-width: 900px;
  margin: 0 auto;
}

/* 页面标题 */
.page-header {
  text-align: center;
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 2px solid var(--el-border-color);
}

.header-icon-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 70px;
  height: 70px;
  background: linear-gradient(to right, #7ef0b3, #9c6edd);
  border-radius: 50%;
  margin-bottom: 1rem;
  box-shadow: 0 4px 15px rgba(126, 240, 179, 0.3);
  animation: float 3s ease-in-out infinite;
}

.dark .header-icon-wrapper {
  background: linear-gradient(to right, #46e2cb, #742bd9);
  box-shadow: 0 4px 15px rgba(70, 226, 203, 0.3);
}

.header-icon {
  font-size: 36px;
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
  margin: 0 0 0.5rem 0;
}

.dark .page-title {
  background: linear-gradient(to right, #46e2cb, #742bd9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  color: var(--el-text-color-regular);
  font-size: 1rem;
  margin: 0;
}

/* 表单卡片 */
.form-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  padding: 2.5rem;
  transition: all 0.3s ease;
}

.form-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
}

/* 区域标题 */
.section-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--el-border-color);
}

.section-icon {
  font-size: 1.5rem;
  color: var(--el-color-primary);
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}

/* 头像上传区域 */
.avatar-section {
  margin-bottom: 2.5rem;
}

.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.avatar-uploader {
  width: 100%;
  max-width: 500px;
}

.avatar-uploader :deep(.el-upload-dragger) {
  width: 100%;
  padding: 3rem 2rem;
  background: var(--el-fill-color-lighter);
  border: 2px dashed var(--el-border-color);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.avatar-uploader :deep(.el-upload-dragger:hover) {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.upload-icon {
  font-size: 4rem;
  color: var(--el-color-primary);
  margin-bottom: 1rem;
}

.upload-text {
  font-size: 1.1rem;
  color: var(--el-text-color-primary);
  margin-bottom: 0.5rem;
}

.upload-text em {
  color: var(--el-color-primary);
  font-style: normal;
  font-weight: 600;
}

.upload-hint {
  font-size: 0.875rem;
  color: var(--el-text-color-regular);
  margin-top: 0.5rem;
}

/* 预览区域 */
.preview-container {
  width: 100%;
  max-width: 300px;
}

.preview-wrapper {
  position: relative;
  width: 200px;
  height: 200px;
  margin: 0 auto;
  border-radius: 12px;
  overflow: hidden;
  border: 3px solid var(--el-color-primary-light-7);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.preview-wrapper:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.15);
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.preview-wrapper:hover .preview-overlay {
  opacity: 1;
}

.delete-button {
  width: 50px;
  height: 50px;
  font-size: 1.5rem;
}

/* 基本信息区域 */
.info-section {
  margin-bottom: 2.5rem;
}

.form-content {
  padding: 1rem 0;
}

.info-form {
  max-width: 600px;
  margin: 0 auto;
}

.form-item-custom {
  margin-bottom: 1.75rem;
}

.form-item-custom :deep(.el-form-item__label) {
  color: var(--el-text-color-primary);
  font-weight: 600;
  font-size: 1rem;
}

.custom-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.custom-input :deep(.el-input__wrapper:hover) {
  border-color: var(--el-color-primary-light-7);
}

.custom-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px var(--el-color-primary-light-8);
}

.custom-select {
  width: 100%;
}

.custom-select :deep(.el-input__wrapper) {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.custom-select :deep(.el-input__wrapper:hover) {
  border-color: var(--el-color-primary-light-7);
}

.custom-select :deep(.el-input__wrapper.is-focus) {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px var(--el-color-primary-light-8);
}

.custom-number-input {
  width: 100%;
}

.custom-number-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  transition: all 0.3s ease;
}

/* 提交按钮区域 */
.submit-section {
  display: flex;
  gap: 1rem;
  justify-content: center;
  padding-top: 2rem;
  border-top: 1px solid var(--el-border-color);
  flex-wrap: wrap;
}

.submit-btn {
  min-width: 200px;
  height: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.4);
}

.cancel-btn {
  min-width: 200px;
  height: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.cancel-btn:hover {
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
@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-wrapper {
    padding: 1rem 0.5rem;
  }

  .form-card {
    padding: 1.5rem;
    border-radius: 12px;
  }

  .page-header {
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
  }

  .header-icon-wrapper {
    width: 60px;
    height: 60px;
  }

  .header-icon {
    font-size: 30px;
  }

  .page-title {
    font-size: 1.75rem;
  }

  .preview-wrapper {
    width: 150px;
    height: 150px;
  }

  .submit-section {
    flex-direction: column;
  }

  .submit-btn,
  .cancel-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .form-card {
    padding: 1.25rem;
  }

  .section-title {
    font-size: 1.1rem;
  }

  .upload-icon {
    font-size: 3rem;
  }

  .upload-text {
    font-size: 1rem;
  }

  .submit-btn,
  .cancel-btn {
    height: 44px;
    font-size: 1rem;
  }
}
</style>  