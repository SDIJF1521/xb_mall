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

              <!-- 商品规格 -->
              <el-form-item label="商品规格" prop="specifications" required>
                <div class="specifications-container">
                  <div v-if="formData.specifications.length === 0" class="spec-empty-tip">
                    <el-alert
                      type="warning"
                      :closable="false"
                      show-icon
                    >
                      <template #title>
                        <span>请至少添加一个商品规格（如：颜色、尺寸等）</span>
                      </template>
                    </el-alert>
                  </div>
                  <div v-for="(spec, specIndex) in formData.specifications" :key="specIndex" class="spec-item">
                    <div class="spec-header">
                      <el-input
                        v-model="spec.name"
                        placeholder="规格名称（如：颜色、尺寸）"
                        size="default"
                        class="spec-name-input"
                        @blur="handleSpecNameBlur"
                      />
                      <el-button
                        type="danger"
                        size="small"
                        :icon="Close"
                        circle
                        @click="removeSpecification(specIndex)"
                        class="remove-spec-btn"
                      />
                    </div>
                    <div class="spec-values">
                      <el-tag
                        v-for="(value, valueIndex) in spec.values"
                        :key="valueIndex"
                        closable
                        @close="removeSpecValue(specIndex, valueIndex)"
                        class="spec-value-tag"
                        effect="plain"
                      >
                        {{ value }}
                      </el-tag>
                      <el-input
                        v-if="spec.inputVisible"
                        ref="specValueInputRef"
                        v-model="spec.inputValue"
                        class="spec-value-input"
                        size="small"
                        @keyup.enter="handleSpecValueConfirm(specIndex)"
                        @blur="handleSpecValueConfirm(specIndex)"
                        placeholder="输入规格值"
                      />
                      <el-button
                        v-else
                        class="add-spec-value-btn"
                        size="small"
                        @click="showSpecValueInput(specIndex)"
                      >
                        <el-icon><Plus /></el-icon>
                        添加值
                      </el-button>
                    </div>
                    <div v-if="spec.name && spec.values.length === 0" class="spec-value-warning">
                      <el-text type="warning" size="small">请为该规格添加至少一个值</el-text>
                    </div>
                  </div>
                  <el-button
                    v-if="formData.specifications.length < 3"
                    type="primary"
                    plain
                    size="default"
                    @click="addSpecification"
                    class="add-spec-btn"
                  >
                    <el-icon><Plus /></el-icon>
                    添加规格
                  </el-button>
                  <div v-if="formData.specifications.length > 0" class="spec-tip">
                    最多可添加3个规格，每个规格可添加多个值
                  </div>
                </div>
              </el-form-item>

              <!-- 规格组合（SKU） -->
              <el-form-item
                v-if="skuList.length > 0"
                label="规格组合"
                prop="skuList"
              >
                <div class="sku-container">
                  <el-table :data="skuList" border stripe class="sku-table">
                    <el-table-column prop="specs" label="规格组合" width="300">
                      <template #default="{ row }">
                        <el-tag
                          v-for="(spec, index) in row.specs"
                          :key="index"
                          class="sku-tag"
                          type="info"
                          effect="plain"
                        >
                          {{ spec }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column label="价格" width="200">
                      <template #default="{ row, $index }">
                        <el-input-number
                          v-model="row.price"
                          :min="0"
                          :precision="2"
                          :step="0.1"
                          size="default"
                          style="width: 100%"
                          @change="updateSkuPrice($index, $event)"
                        />
                      </template>
                    </el-table-column>
                    <el-table-column label="库存" width="200">
                      <template #default="{ row, $index }">
                        <el-input-number
                          v-model="row.stock"
                          :min="0"
                          :step="1"
                          size="default"
                          style="width: 100%"
                          @change="updateSkuStock($index, $event)"
                        />
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
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
  Close,
  Delete
} from '@element-plus/icons-vue'

import { useRoute } from 'vue-router'
import axios from 'axios';
const file_name = ['png', 'jpg', 'jpeg']

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

interface Specification {
    name: string;
    values: string[];
    inputVisible: boolean;
    inputValue: string;
}

interface SkuItem {
    specs: string[];
    price: number;
    stock: number;
}

interface CommodityAddFormData {
    name: string;
    price: number;
    stock: number;
    description: string;
    category_id: number;
    image: (File | string)[];
    imageUrls: string[];
    tags: string[];
    specifications: Specification[];
    skuList: SkuItem[];
}

const formRef = ref()
const tagInputRef = ref()
const specValueInputRef = ref()
const submitLoading = ref(false)
const previewDialogVisible = ref(false)
const previewImageUrl = ref('')
const inputVisible = ref(false)
const inputValue = ref('')
const skuList = ref<SkuItem[]>([])

const formData = ref<CommodityAddFormData>({
    name: '',
    price: 0,
    stock: 0,
    description: '',
    category_id: 0,
    image: [],
    imageUrls: [],
    tags: [],
    specifications: [],
    skuList: [],
})

// 验证规格的自定义验证函数
const validateSpecifications = (rule: any, value: any, callback: any) => {
    const validSpecs = formData.value.specifications.filter(spec => 
        spec.name.trim() && spec.values.length > 0
    )
    
    if (validSpecs.length === 0) {
        callback(new Error('请至少添加一个商品规格，并为每个规格添加至少一个值'))
    } else {
        callback()
    }
}

const rules = ref({
    name: [
        { required: true, message: '请输入商品名称', trigger: 'blur' },
        { min: 2, max: 50, message: '商品名称长度应在 2 到 50 个字符之间', trigger: 'blur' }
    ],
    description: [
        { required: true, message: '请输入商品描述', trigger: 'blur' },
        { min: 10, max: 500, message: '商品描述长度应在 10 到 500 个字符之间', trigger: 'blur' }
    ],
    category_id: [{ required: true, message: '请选择商品分类', trigger: 'change' }],
    image: [{ required: true, message: '请上传商品图片', trigger: 'change' }],
    tags: [{ type: 'array', max: 8, message: '最多只能添加8个标签', trigger: 'change' }],
    specifications: [
        { validator: validateSpecifications, trigger: 'change' }
    ],
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
    // 检查文件类型是否为图片
    const fileExtension = uploadFile.name.split('.').pop().toLowerCase()
    if (!file_name.includes(fileExtension)) {
        ElMessage.error('只能上传图片文件!')
        return false
    }

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

    await formRef.value.validate(async (valid: boolean) => {
        if (valid) {
            submitLoading.value = true
            const commitFormData = new FormData()
            commitFormData.append('token', token||'')
            commitFormData.append('stroe_id', id.toString())
            commitFormData.append('name', formData.value.name)

            // Send only the first tag as type (since backend expects Tuple[str])
            if (formData.value.tags.length > 0) {
                commitFormData.append('type', formData.value.tags.join(','))
            }

            formData.value.image.forEach((file: any) => {
                commitFormData.append('img_list', file.raw)
            })

            // 验证至少有一个有效的规格
            const validSpecs = formData.value.specifications.filter(spec => 
                spec.name.trim() && spec.values.length > 0
            )
            
            if (validSpecs.length === 0) {
                ElMessage.error('请至少添加一个商品规格，并为每个规格添加至少一个值！')
                submitLoading.value = false
                return false
            }
            
            // 验证SKU列表是否存在
            if (skuList.value.length === 0) {
                ElMessage.error('规格组合生成失败，请检查规格设置！')
                submitLoading.value = false
                return false
            }
            
            // 验证SKU列表中的价格和库存
            const invalidSku = skuList.value.find(sku => sku.price <= 0 || sku.stock < 0)
            if (invalidSku) {
                ElMessage.error('请为所有规格组合设置有效的价格（>0）和库存（≥0）！')
                submitLoading.value = false
                return false
            }
            
            // 将SKU列表转换为JSON字符串发送
            commitFormData.append('sku_list', JSON.stringify(skuList.value))
            commitFormData.append('classify_categorize', formData.value.category_id.toString())
            commitFormData.append('info', formData.value.description)

            console.log(formData.value.image);
            try{
              const res = await Axios.post('/buyer_commodity_add',commitFormData)
              if (res.status == 200){
                if (res.data.current){
                  ElMessage.success('商品添加成功！')
                  formData.value = {
                    name: '',
                    price: 0,
                    stock: 0,
                    description: '',
                    category_id: 0,
                    image: [],
                    imageUrls: [],
                    tags: [],
                    specifications: [],
                    skuList: [],
                  }
                  skuList.value = []
                  submitLoading.value = false
                  return true
                }else{
                  ElMessage.error('商品添加失败！')
                  submitLoading.value = false
                  return false
                }
              }else{
                  ElMessage.error('商品添加失败！')
                  submitLoading.value = false
                  return false
              }
            } catch (error) {
                ElMessage.error('商品添加失败！')
                submitLoading.value = false
                return false
            }
        } else {
            ElMessage.error('请完善表单信息')
            submitLoading.value = false
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

// 规格相关函数
const addSpecification = () => {
    if (formData.value.specifications.length >= 3) {
        ElMessage.warning('最多只能添加3个规格!')
        return
    }
    formData.value.specifications.push({
        name: '',
        values: [],
        inputVisible: false,
        inputValue: ''
    })
}

const removeSpecification = (index: number) => {
    formData.value.specifications.splice(index, 1)
    generateSkuCombinations()
    // 触发验证
    nextTick(() => {
        formRef.value?.validateField('specifications')
    })
}

const showSpecValueInput = (specIndex: number) => {
    formData.value.specifications[specIndex].inputVisible = true
    nextTick(() => {
        // 聚焦到输入框
        const inputs = document.querySelectorAll('.spec-value-input')
        if (inputs[specIndex]) {
            (inputs[specIndex] as HTMLInputElement).focus()
        }
    })
}

const handleSpecValueConfirm = (specIndex: number) => {
    const spec = formData.value.specifications[specIndex]
    if (spec.inputValue) {
        const value = spec.inputValue.trim()
        if (value && !spec.values.includes(value)) {
            spec.values.push(value)
            generateSkuCombinations()
            // 触发验证
            nextTick(() => {
                formRef.value?.validateField('specifications')
            })
        } else if (spec.values.includes(value)) {
            ElMessage.warning('该规格值已存在!')
        }
    }
    spec.inputVisible = false
    spec.inputValue = ''
}

const removeSpecValue = (specIndex: number, valueIndex: number) => {
    formData.value.specifications[specIndex].values.splice(valueIndex, 1)
    generateSkuCombinations()
    // 触发验证
    nextTick(() => {
        formRef.value?.validateField('specifications')
    })
}

// 处理规格名称失焦
const handleSpecNameBlur = () => {
    generateSkuCombinations()
    // 触发验证
    nextTick(() => {
        formRef.value?.validateField('specifications')
    })
}

// 生成SKU组合
const generateSkuCombinations = () => {
    const specs = formData.value.specifications.filter(spec => 
        spec.name.trim() && spec.values.length > 0
    )
    
    if (specs.length === 0) {
        skuList.value = []
        return
    }

    // 生成所有可能的组合
    const combinations: string[][] = []
    
    function generateCombinations(index: number, current: string[]) {
        if (index === specs.length) {
            combinations.push([...current])
            return
        }
        
        for (const value of specs[index].values) {
            current.push(`${specs[index].name}:${value}`)
            generateCombinations(index + 1, current)
            current.pop()
        }
    }
    
    generateCombinations(0, [])
    
    // 更新SKU列表，保留已有的价格和库存
    const existingSkus = new Map<string, SkuItem>()
    skuList.value.forEach(sku => {
        const key = sku.specs.join('|')
        existingSkus.set(key, sku)
    })
    
    skuList.value = combinations.map(combo => {
        const key = combo.join('|')
        const existing = existingSkus.get(key)
        return existing || {
            specs: combo,
            price: 0,
            stock: 0
        }
    })
}

const updateSkuPrice = (index: number, price: number) => {
    if (skuList.value[index]) {
        skuList.value[index].price = price || 0
    }
}

const updateSkuStock = (index: number, stock: number) => {
    if (skuList.value[index]) {
        skuList.value[index].stock = stock || 0
    }
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

/* 规格相关样式 */
.specifications-container {
  width: 100%;
}

.spec-item {
  margin-bottom: 20px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
  transition: all 0.3s ease;
}

.spec-item:hover {
  border-color: #409eff;
  background: #f0f7ff;
}

.spec-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.spec-name-input {
  flex: 1;
}

.remove-spec-btn {
  flex-shrink: 0;
}

.spec-values {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.spec-value-tag {
  margin: 0;
}

.spec-value-input {
  width: 120px;
}

.add-spec-value-btn {
  border-style: dashed;
}

.add-spec-btn {
  width: 100%;
  margin-top: 12px;
  border-style: dashed;
}

.spec-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.spec-empty-tip {
  margin-bottom: 16px;
}

.spec-value-warning {
  margin-top: 8px;
  padding: 8px 12px;
  background: #fef0f0;
  border: 1px solid #fde2e2;
  border-radius: 4px;
}

/* SKU表格样式 */
.sku-container {
  width: 100%;
  margin-top: 12px;
}

.sku-table {
  width: 100%;
}

.sku-tag {
  margin-right: 8px;
  margin-bottom: 4px;
}

:deep(.sku-table .el-table__header) {
  background-color: #f5f7fa;
}

:deep(.sku-table .el-table__row:hover) {
  background-color: #f0f7ff;
}
</style>
