<template>
  <div class="commodity-add-container">
    <el-card class="commodity-add-card">
      <template #header>
        <div class="card-header">
          <el-icon><Goods /></el-icon>
          <span class="card-title">添加新商品</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="120px"
        class="commodity-form"
        @submit.prevent="handleSubmit"
      >
        <el-row :gutter="24">
          <!-- 左侧基本信息 -->
          <el-col :span="12">
            <div class="form-section">
              <h3 class="section-title">基本信息</h3>

              <el-form-item label="商品名称" prop="name">
                <el-input
                  v-model="formData.name"
                  placeholder="请输入商品名称"
                  size="large"
                  clearable
                >
                  <template #prefix>
                    <el-icon><Edit /></el-icon>
                  </template>
                </el-input>
              </el-form-item>

              <el-form-item label="商品价格" prop="price">
                <el-input-number
                  v-model="formData.price"
                  :min="0"
                  :precision="2"
                  :step="0.1"
                  placeholder="请输入商品价格"
                  size="large"
                  style="width: 100%"
                >
                  <template #prefix>
                    <span style="color: #f56c6c">¥</span>
                  </template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="商品库存" prop="stock">
                <el-input-number
                  v-model="formData.stock"
                  :min="0"
                  :step="1"
                  placeholder="请输入商品库存数量"
                  size="large"
                  style="width: 100%"
                >
                  <template #prefix>
                    <el-icon><Box /></el-icon>
                  </template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="商品分类" prop="category_id">
                <el-select
                  v-model="formData.category_id"
                  placeholder="请选择商品分类"
                  size="large"
                  clearable
                  style="width: 100%"
                >
                  <el-option
                    v-for="item in classifyList"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="商品描述" prop="description">
                <el-input
                  v-model="formData.description"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入商品描述，详细介绍商品的特点和优势..."
                  maxlength="500"
                  show-word-limit
                />
              </el-form-item>

              <el-form-item label="商品标签" prop="tags">
                <div class="tags-container">
                  <el-tag
                    v-for="(tag, index) in formData.tags"
                    :key="index"
                    closable
                    @close="removeTag(index)"
                    class="commodity-tag"
                    type="info"
                    effect="light"
                  >
                    {{ tag }}
                  </el-tag>
                  <el-input
                    v-if="inputVisible"
                    ref="tagInputRef"
                    v-model="inputValue"
                    class="tag-input"
                    size="small"
                    @keyup.enter="handleTagInputConfirm"
                    @blur="handleTagInputConfirm"
                    placeholder="输入标签"
                  />
                  <el-button
                    v-else
                    class="add-tag-btn"
                    size="small"
                    @click="showTagInput"
                    :disabled="formData.tags.length >= 8"
                  >
                    <el-icon><Plus /></el-icon>
                    添加标签
                  </el-button>
                </div>
                <div class="tag-tip">最多可添加8个标签，按回车确认</div>
              </el-form-item>
            </div>
          </el-col>

          <!-- 右侧图片上传 -->
          <el-col :span="8">
            <div class="form-section">
              <h3 class="section-title">商品图片</h3>

              <el-form-item label="商品图片" prop="image">
                <el-upload
                  v-model:file-list="formData.image"
                  class="image-uploader"
                  action="#"
                  multiple
                  :limit="5"
                  :on-change="handleImageChange"
                  :on-remove="handleImageRemove"
                  :on-exceed="handleImageExceed"
                  :on-preview="handleImagePreview"
                  list-type="picture-card"
                  accept="image/*"
                  :auto-upload="false"
                >
                  <el-icon class="upload-icon"><Plus /></el-icon>
                  <div class="upload-text">点击或拖拽上传</div>
                  <div class="upload-tip">最多5张图片</div>
                </el-upload>
              </el-form-item>
            </div>
          </el-col>
        </el-row>

        <!-- 提交按钮 -->
        <el-form-item class="form-actions">
          <el-button type="info" @click="handleReset" size="large" style="width: 40%;">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
          <el-button type="primary" @click="handleSubmit" size="large" :loading="submitLoading" style="width: 40%;">
            <el-icon><Check /></el-icon>
            提交商品
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>

  <!-- 图片预览对话框 -->
  <el-dialog
    v-model="previewDialogVisible"
    title="图片预览"
    width="80%"
    top="5vh"
    :close-on-click-modal="true"
    :close-on-press-escape="true"
    @close="closePreview"
  >
    <div class="preview-dialog-content">
      <img
        :src="previewImageUrl"
        alt="预览图片"
        class="preview-image-large"
      />
    </div>
    <template #footer>
      <div class="preview-dialog-footer">
        <el-button @click="closePreview" size="large">
          <el-icon><Close /></el-icon>
          关闭
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>
<script setup lang="ts">
import { ref, computed, onUnmounted, watch, nextTick,onMounted} from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Goods,
  Edit,
  Box,
  Plus,
  Refresh,
  Check,

  Close
} from '@element-plus/icons-vue'

import { useRoute } from 'vue-router'
import axios from 'axios';


defineOptions({
    name: 'CommodityAdd',
})

const Axios = axios.create({
    baseURL: "http://127.0.0.1:8000/api",
})

const id = useRoute().params.id
const token = localStorage.getItem('buyer_access_token')

interface ClassifyOption {
    label: string;
    value: number;
}

const classifyList = ref<ClassifyOption[]>([])

interface CommodityAddFormData {
    name: string;
    price: number;
    stock: number;
    description: string;
    category_id: number;
    image: (File | string)[];
    imageUrls: string[];
    tags: string[];
}

const formRef = ref()
const tagInputRef = ref()
const submitLoading = ref(false)
const previewDialogVisible = ref(false)
const previewImageUrl = ref('')
const inputVisible = ref(false)
const inputValue = ref('')

const formData = ref<CommodityAddFormData>({
    name: '',
    price: 0,
    stock: 0,
    description: '',
    category_id: 0,
    image: [],
    imageUrls: [],
    tags: [],
})

const rules = ref({
    name: [
        { required: true, message: '请输入商品名称', trigger: 'blur' },
        { min: 2, max: 50, message: '商品名称长度应在 2 到 50 个字符之间', trigger: 'blur' }
    ],
    price: [
        { required: true, message: '请输入商品价格', trigger: 'blur' },
        { type: 'number', min: 0, message: '价格不能为负数', trigger: 'blur' }
    ],
    stock: [
        { required: true, message: '请输入商品库存', trigger: 'blur' },
        { type: 'number', min: 0, message: '库存不能为负数', trigger: 'blur' }
    ],
    description: [
        { required: true, message: '请输入商品描述', trigger: 'blur' },
        { min: 10, max: 500, message: '商品描述长度应在 10 到 500 个字符之间', trigger: 'blur' }
    ],
    category_id: [{ required: true, message: '请选择商品分类', trigger: 'change' }],
    image: [{ required: true, message: '请上传商品图片', trigger: 'change' }],
    tags: [{ type: 'array', max: 8, message: '最多只能添加8个标签', trigger: 'change' }],
})

onMounted(async () =>{
    try {
        const response = await Axios.get('/buter_get_classify',{
            params: {
                store_id: id
            },
            headers: {
                'access-token': token
            }
        })
        if (response.data.current) {
           console.log(response.data.data);

            for (const item in response.data.data) {

                classifyList.value.push({
                    label: response.data.data[item],
                    value: Number(item)
                })
            }
        }
    } catch (error) {
        ElMessage.error('获取分类失败')
    }
})


// 文件选择变化处理
const handleImageChange = (uploadFile: any) => {
    // Element Plus 会自动处理文件列表，这里只需要验证文件类型和大小
    if (uploadFile.raw) {
        const isImage = uploadFile.raw.type.startsWith('image/')
        const isLt5M = uploadFile.raw.size / 1024 / 1024 < 5

        if (!isImage) {
            ElMessage.error('只能上传图片文件!')
            return false
        }
        if (!isLt5M) {
            ElMessage.error('图片大小不能超过 5MB!')
            return false
        }
    }
}

// 处理文件超出限制
const handleImageExceed = () => {
    ElMessage.warning('最多只能上传5张图片!')
}

// 处理文件移除
const handleImageRemove = (file: any) => {
    // Element Plus 会自动从 file-list 中移除文件，这里不需要手动处理
    // 只需要清理预览URL（如果有）
    if (file.url && file.url.startsWith('blob:')) {
        URL.revokeObjectURL(file.url)
    }
}

// 处理图片预览
const handleImagePreview = (file: any) => {
    if (file.url) {
        previewImageUrl.value = file.url
    } else if (file.raw instanceof File) {
        previewImageUrl.value = URL.createObjectURL(file.raw)
    }
    previewDialogVisible.value = true
}

// 关闭预览对话框
const closePreview = () => {
    previewDialogVisible.value = false
    previewImageUrl.value = ''
}

// 清理预览URL
const cleanupPreview = () => {
    // 清理当前预览图片的URL
    if (previewImageUrl.value && previewImageUrl.value.startsWith('blob:')) {
        URL.revokeObjectURL(previewImageUrl.value)
    }
    previewImageUrl.value = ''
}

// 监听图片变化，清理预览URL
watch(() => formData.value.image, () => {
    // 当图片列表变化时，清理当前预览URL
    cleanupPreview()
}, { deep: true })

// 重置表单
const handleReset = () => {
    ElMessageBox.confirm(
        '确定要重置所有表单内容吗？',
        '重置确认',
        {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
        }
    ).then(() => {
        formRef.value?.resetFields()
        cleanupPreview()
        ElMessage.success('表单已重置')
    }).catch(() => {
        // 用户取消重置
    })
}

// 提交表单
const handleSubmit = async () => {
    if (!formRef.value) return

    await formRef.value.validate((valid: boolean) => {
        if (valid) {
            submitLoading.value = true

            // 模拟提交过程
            setTimeout(() => {
                ElMessage.success('商品添加成功！')
                submitLoading.value = false
                // 这里可以添加实际的API调用逻辑
                console.log('提交的数据:', formData.value)
            }, 2000)
        } else {
            ElMessage.error('请完善表单信息')
            return false
        }
    })
}

// 标签相关函数
const showTagInput = () => {
    inputVisible.value = true
    nextTick(() => {
        tagInputRef.value?.focus()
    })
}

const handleTagInputConfirm = () => {
    if (inputValue.value) {
        const tagValue = inputValue.value.trim()
        if (tagValue && !formData.value.tags.includes(tagValue)) {
            if (formData.value.tags.length < 8) {
                formData.value.tags.push(tagValue)
            } else {
                ElMessage.warning('最多只能添加8个标签!')
            }
        }
    }
    inputVisible.value = false
    inputValue.value = ''
}

const removeTag = (index: number) => {
    formData.value.tags.splice(index, 1)
}

// 组件卸载时清理资源
onUnmounted(() => {
    cleanupPreview()
})

</script>

<style scoped>
.commodity-add-container {
  padding: 20px;
  min-height: 73=4vh;
}

.commodity-add-card {
  max-width: 1200px;
  margin: 0 auto;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
}

.card-header .el-icon {
  font-size: 24px;
  color: #409eff;
}

.card-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.commodity-form {
  padding: 20px 0;
}

.form-section {
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #495057;
  margin: 0 0 20px 0;
  padding-bottom: 10px;
  border-bottom: 2px solid #90bae5;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #495057;
  font-size: 14px;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.2);
}

:deep(.el-input-number) {
  border-radius: 8px;
}

:deep(.el-select__wrapper) {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

:deep(.el-select__wrapper:hover) {
  border-color: #409eff;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

:deep(.el-select__wrapper.is-focused) {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.2);
}

:deep(.el-textarea__inner) {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  font-family: inherit;
  line-height: 1.6;
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

:deep(.el-textarea__inner:hover) {
  border-color: #409eff;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

:deep(.el-textarea__inner:focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.2);
}

.image-uploader {
  width: 100%;
}

:deep(.el-upload--picture-card) {
  border-radius: 12px;
  transition: all 0.3s ease;
  width: 120px;
  height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

:deep(.el-upload--picture-card:hover) {
  border-color: #409eff;
  background: #f0f7ff;
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(64, 158, 255, 0.2);
}

:deep(.el-upload-list--picture-card) {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

:deep(.el-upload-list__item) {
  width: 120px;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
}

:deep(.el-upload-list__item:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.upload-icon {
  font-size: 32px;
  color: #8c939d;
  margin-bottom: 8px;
}

.upload-text {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
  font-weight: 500;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
  text-align: center;
}

.image-preview-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
}

.preview-item {
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.preview-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.preview-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.preview-item:hover .preview-overlay {
  opacity: 1;
}

.remove-btn {
  background: #f56c6c;
  border: none;
  color: white;
}

.remove-btn:hover {
  background: #f78989;
  transform: scale(1.1);
}

.form-actions {
  margin-top: 30px;
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid  #409eff;
}

.form-actions .el-button {
  margin: 0 12px;
  min-width: 120px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.form-actions .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .commodity-add-container {
    padding: 10px;
  }

  .form-section {
    padding: 16px;
  }

  .card-title {
    font-size: 20px;
  }

  :deep(.el-form-item__label) {
    width: 100px !important;
  }

  .form-actions .el-button {
    margin: 8px;
    min-width: 100px;
  }
}

/* 动画效果 */
.commodity-add-card {
  animation: fadeInUp 0.6s ease-out;
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

.form-section {
  animation: slideInLeft 0.8s ease-out;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 图片预览对话框样式 */
.preview-dialog-content {
  text-align: center;
  padding: 20px;
}

.preview-image-large {
  max-width: 100%;
  max-height: 70vh;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s ease;
}

.preview-image-large:hover {
  transform: scale(1.02);
}

.preview-dialog-footer {
  text-align: center;
  padding: 16px 0;
}

:deep(.el-dialog__body) {
  padding: 0;
}

:deep(.el-dialog__header) {
  margin: 0;
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

:deep(.el-dialog__footer) {
  padding: 16px 20px;
  border-top: 1px solid #e4e7ed;
}
</style>
