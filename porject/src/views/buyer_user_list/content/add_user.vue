<template>
  <div class="add-user-container">

    <el-form ref="formRef" :model="formData" label-width="120px" class="user-form">
      <el-row :gutter="30">
        <el-col :span="12">
          <div class="form-section">
            <div class="section-title">
              <el-icon><Edit /></el-icon>
              <span>基本信息</span>
            </div>

            <el-form-item label="用户名" prop="name">
              <el-input v-model="formData.name" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="formData.password" type="password" placeholder="请输入密码" show-password />
            </el-form-item>
            <el-form-item label="权限" prop="authority">
              <el-radio-group v-model="formData.authority" class="authority-radio-group">
                <el-radio label="0" border>普通用户</el-radio>
                <el-radio label="1" border>管理员</el-radio>
                <el-radio label="2" border>超级管理员</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="formData.email" type="email" placeholder="请输入邮箱地址" />
            </el-form-item>
          </div>
        </el-col>

          <!--图片上传-->
          <el-col :span="12">
            <div class="form-section">
              <div class="section-title">
                <el-icon><Picture /></el-icon>
                <span>用户头像</span>
              </div>

              <div class="upload-section">
                <el-upload
                  class="upload-area"
                  drag
                  action="#"
                  :limit="1"
                  :file-list="uploadFileList"
                  :on-change="handlePictureChange"
                  :auto-upload="false"
                  accept="image/*"
                >
                  <div v-if="!previewImage" class="upload-placeholder">
                    <el-icon class="upload-icon-large"><Plus /></el-icon>
                    <div class="upload-text-main">点击或拖拽上传图片</div>
                    <div class="upload-text-sub">支持 JPG、PNG、GIF 格式</div>
                  </div>
                  <div v-else class="uploaded-file">
                    <img :src="previewImage" class="uploaded-image" @click="showPreviewImage" />
                    <div class="uploaded-text">{{ uploadFileList[0]?.name }}</div>
                  </div>
                  <template #tip>
                    <div class="upload-tip">
                      <el-icon><InfoFilled /></el-icon>
                      <span>建议上传 200x200 像素的正方形图片，支持 JPG、PNG、GIF 格式，文件大小不超过 2MB</span>
                    </div>
                  </template>
                </el-upload>

                <!-- 图片预览区域 -->
                <div v-if="previewImage" class="preview-container">
                  <div class="preview-header">
                    <el-icon><Picture /></el-icon>
                    <span>图片预览</span>
                  </div>
                  <div class="preview-images">
                    <div class="preview-item" @click="showPreviewImage">
                      <img :src="previewImage" class="preview-image" />
                      <el-button
                        class="remove-btn"
                        type="danger"
                        size="small"
                        circle
                        @click.stop="removePreviewImage"
                      >
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 图片预览对话框 -->
              <el-dialog
                v-model="previewDialogVisible"
                title="图片预览"
                width="600px"
                center
                append-to-body
                custom-class="preview-dialog"
              >
                <div class="preview-dialog-content">
                  <img :src="previewImage" class="preview-dialog-image" />
                </div>
                <template #footer>
                  <el-button @click="closePreview" type="primary">关闭</el-button>
                </template>
              </el-dialog>
            </div>
          </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-button type="primary" style="width: 100%;">提交</el-button>
        </el-col>
        <el-col :span="12">
          <el-button type="primary" style="width: 100%;">关闭</el-button>
      </el-col>
    </el-row>
    </el-form>

  </div>
</template>
<script setup lang="ts">

import {ref,onMounted,reactive} from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Picture, Plus, InfoFilled, User, Edit } from '@element-plus/icons-vue'

defineOptions({
    name: 'AddUser',
})

interface FormData{
  name: string
  password: string
  authority:number
  img: File | null
  email:string
}

const formData = reactive<FormData>({
  name: '',
  password: '',
  authority: 0,
  img: null,
  email: ''
})

// 上传相关状态
const uploadFileList = ref<any[]>([])
const previewImage = ref<string>('')
const previewDialogVisible = ref<boolean>(false)

// 图片处理函数
const handlePictureChange = async (file: any) => {
  try {
    const base64String = await fileToBase64(file.raw)
    previewImage.value = base64String
    formData.img = file.raw

    // 更新上传文件列表
    uploadFileList.value = [{
      name: file.name,
      url: base64String,
      raw: file.raw
    }]
  } catch (error) {
    console.error('文件转换失败:', error)
    ElMessage.error('图片处理失败')
  }
}

// 删除预览图片
const removePreviewImage = () => {
  previewImage.value = ''
  formData.img = null
  uploadFileList.value = []
}

// 预览图片
const showPreviewImage = () => {
  previewDialogVisible.value = true
}

// 关闭预览对话框
const closePreview = () => {
  previewDialogVisible.value = false
}

// 文件对象转B64字符串
const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = error => reject(error)
  })
}
</script>
<style scoped>
/* 整体容器美化 */
.add-user-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}


@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}


/* 表单区域美化 */
.user-form {
  background: var(--el-fill-color-blank);
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
}

.form-section {
  padding: 30px 20px;
  height: 100%;
}

.section-title {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--el-color-primary-light-8);
  color: var(--el-text-color-primary);
  font-size: 18px;
  font-weight: 600;
}

.section-title .el-icon {
  font-size: 20px;
  color: var(--el-color-primary);
  margin-right: 8px;
}

/* 表单整体美化 */
.el-form {
  padding: 20px;
  background: var(--el-fill-color-blank);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

/* 表单项美化 */
.el-form-item {
  margin-bottom: 20px;
}

.el-form-item__label {
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-size: 14px;
}

/* 输入框美化 */
.el-input {
  border-radius: 8px;
}

.el-input__inner {
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  transition: all 0.3s ease;
}

.el-input__inner:focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

/* 权限单选框美化 */
.authority-radio-group {
  display: flex;
  gap: 12px;
}

.authority-radio-group .el-radio {
  margin-right: 0;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.authority-radio-group .el-radio.is-checked {
  background-color: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary);
}

/* 上传区域样式 */
.upload-section {
  margin-top: 10px;
}

.upload-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  color: var(--el-text-color-primary);
  font-weight: 600;
  font-size: 16px;
}

.upload-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.upload-icon {
  font-size: 18px;
  color: var(--el-color-primary);
  margin-right: 8px;
}

.upload-text {
  font-size: 14px;
  font-weight: 500;
}

.upload-area {
  width: 100%;
  height: 180px;
  border-radius: 8px;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color);
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  height: 100%;
  border: none;
  background: transparent;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.upload-icon-large {
  font-size: 48px;
  color: var(--el-color-primary);
  margin-bottom: 16px;
}

.upload-text-main {
  font-size: 16px;
  color: var(--el-text-color-primary);
  font-weight: 500;
  margin-bottom: 8px;
}

.upload-text-sub {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

/* 上传提示样式 */
.upload-tip {
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--el-color-info-light-9);
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--el-color-info);
  line-height: 1.4;
}

.upload-tip .el-icon {
  font-size: 14px;
  color: var(--el-color-info);
}

/* 已上传文件显示样式 */
.uploaded-file {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
}

.uploaded-image {
  max-width: 120px;
  max-height: 120px;
  object-fit: contain;
  border-radius: 8px;
  margin-bottom: 8px;
}

.uploaded-text {
  font-size: 14px;
  color: var(--el-text-color-regular);
  text-align: center;
  word-break: break-all;
}

/* 图片预览区域样式 */
.preview-container {
  margin-top: 20px;
  padding: 15px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}

.preview-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.preview-header el-icon {
  margin-right: 8px;
  color: var(--el-color-primary);
}

.preview-images {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.preview-item {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--el-border-color);
  cursor: pointer;
  transition: all 0.3s ease;
}

.preview-item:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.preview-item:hover .remove-btn {
  opacity: 1;
}

/* 预览对话框样式 */
.preview-dialog-content {
  text-align: center;
  padding: 20px;
}

.preview-dialog-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 对话框自定义样式 */
.preview-dialog {
  border-radius: 12px;
  overflow: hidden;
}

.preview-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%);
  color: white;
  padding: 16px 20px;
  margin: 0;
}

.preview-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
  font-size: 16px;
}

.preview-dialog :deep(.el-dialog__headerbtn) {
  top: 16px;
  right: 20px;
}

.preview-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 18px;
}

.preview-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: var(--el-color-primary-light-7);
}

/* 按钮美化样式 */
.button-row {
  margin-top: 30px;
  padding: 20px;
  background: var(--el-fill-color-lighter);
  border-radius: 12px;
  display: flex;
  justify-content: center;
  gap: 20px;
}

.button-row .el-col {
  display: flex;
  justify-content: center;
}

.button-row .el-button {
  min-width: 120px;
  height: 44px;
  border-radius: 22px;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.button-row .el-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s ease;
}

.button-row .el-button:hover::before {
  left: 100%;
}

.button-row .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(64, 158, 255, 0.3);
}

.button-row .el-button:active {
  transform: translateY(0);
  box-shadow: 0 4px 15px rgba(64, 158, 255, 0.2);
}

/* 提交按钮特殊样式 */
.button-row .el-button[type="primary"]:first-child {
  background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%);
  border: none;
}

.button-row .el-button[type="primary"]:first-child:hover {
  background: linear-gradient(135deg, var(--el-color-primary-light-1) 0%, var(--el-color-primary-light-2) 100%);
  box-shadow: 0 8px 25px rgba(64, 158, 255, 0.4);
}

/* 重置按钮特殊样式 */
.button-row .el-button[type="primary"]:nth-child(2) {
  background: linear-gradient(135deg, var(--el-color-success) 0%, var(--el-color-success-light-3) 100%);
  border: none;
}

.button-row .el-button[type="primary"]:nth-child(2):hover {
  background: linear-gradient(135deg, var(--el-color-success-light-1) 0%, var(--el-color-success-light-2) 100%);
  box-shadow: 0 8px 25px rgba(103, 194, 58, 0.4);
}

/* 关闭按钮特殊样式 */
.button-row .el-button[type="primary"]:last-child {
  background: linear-gradient(135deg, var(--el-color-warning) 0%, var(--el-color-warning-light-3) 100%);
  border: none;
}

.button-row .el-button[type="primary"]:last-child:hover {
  background: linear-gradient(135deg, var(--el-color-warning-light-1) 0%, var(--el-color-warning-light-2) 100%);
  box-shadow: 0 8px 25px rgba(230, 162, 60, 0.4);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .add-user-container {
    padding: 20px 10px;
  }


  .header-icon {
    font-size: 36px;
    margin-bottom: 12px;
  }

  .header-title {
    font-size: 24px;
  }

  .header-subtitle {
    font-size: 14px;
  }

  .form-section {
    padding: 20px 15px;
  }

  .section-title {
    font-size: 16px;
    margin-bottom: 20px;
  }

  .upload-area {
    height: 150px;
  }

  .upload-icon-large {
    font-size: 36px;
    margin-bottom: 12px;
  }

  .upload-text-main {
    font-size: 14px;
  }

  .upload-text-sub {
    font-size: 12px;
  }

  .preview-item {
    width: 80px;
    height: 80px;
  }

  .upload-tip {
    font-size: 11px;
    padding: 6px 10px;
  }

  .el-form {
    padding: 15px;
  }

  .authority-radio-group {
    flex-direction: column;
    gap: 8px;
  }

  .authority-radio-group .el-radio {
    width: 100%;
    text-align: center;
  }
}
</style>
