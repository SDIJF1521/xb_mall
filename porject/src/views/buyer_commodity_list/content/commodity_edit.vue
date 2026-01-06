<template>
  <div class="commodity-edit-container">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      class="commodity-form"
      @submit.prevent="handleSubmit"
    >
      <el-row :gutter="24">
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
                  :key="item.value"
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
                placeholder="请输入商品描述"
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

        <el-col :span="12">
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

      <el-form-item class="form-actions">
        <el-button type="info" @click="handleCancel" size="large" style="width: 40%;">
          <el-icon><Close /></el-icon>
          取消
        </el-button>
        <el-button type="primary" @click="handleSubmit" size="large" :loading="submitLoading" style="width: 40%;">
          <el-icon><Check /></el-icon>
          保存修改
        </el-button>
      </el-form-item>
    </el-form>

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
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Edit,
  Plus,
  Check,
  Close,
} from '@element-plus/icons-vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

defineOptions({
  name: 'CommodityEdit',
})

const props = defineProps<{
  commodity: {
    id: number
    name: string
    img_list?: string[]
    info: string
    specification_list?: any[]
    types?: string[]
    classify_categorize?: string | number
    audit: number
    time: string
  } | null
}>()

const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'success'): void
}>()

const file_name = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg']
const Axios = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
})

const route = useRoute()
const id = ref(route.params.id)
const token = ref(localStorage.getItem('buyer_access_token') || '')

interface ClassifyOption {
  label: string
  value: number
}

const classifyList = ref<ClassifyOption[]>([])

interface Specification {
  name: string
  values: string[]
  inputVisible: boolean
  inputValue: string
}

interface SkuItem {
  specs: string[]
  price: number
  stock: number
}

interface CommodityEditFormData {
  name: string
  description: string
  category_id: number
  image: any[]
  tags: string[]
  specifications: Specification[]
  skuList: SkuItem[]
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

const formData = ref<CommodityEditFormData>({
  name: '',
  description: '',
  category_id: 0,
  image: [],
  tags: [],
  specifications: [],
  skuList: [],
})

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

const resetFormData = () => {
  formData.value = {
    name: '',
    description: '',
    category_id: 0,
    image: [],
    tags: [],
    specifications: [],
    skuList: [],
  }
  skuList.value = []
  inputVisible.value = false
  inputValue.value = ''
  
  nextTick(() => {
    formRef.value?.clearValidate()
  })
}

const initFormData = () => {
  if (!props.commodity) {
    resetFormData()
    return
  }

  resetFormData()

  formData.value.name = props.commodity.name || ''
  formData.value.description = props.commodity.info || ''
  formData.value.category_id = Number(props.commodity.classify_categorize) || 0
  formData.value.tags = props.commodity.types ? [...props.commodity.types] : []

  if (props.commodity.img_list && props.commodity.img_list.length > 0) {
    formData.value.image = props.commodity.img_list.map((imgBase64, index) => {
      return {
        uid: `existing-${props.commodity?.id}-${index}`,
        name: `image-${index}.jpg`,
        url: `data:image/jpeg;base64,${imgBase64}`,
        isExisting: true,
        base64: imgBase64
      }
    })
  } else {
    formData.value.image = []
  }

  if (props.commodity.specification_list && props.commodity.specification_list.length > 0) {
    const specMap = new Map<string, Set<string>>()
    
    props.commodity.specification_list.forEach((sku: any) => {
      if (sku.specs && Array.isArray(sku.specs)) {
        sku.specs.forEach((specStr: string) => {
          const [specName, specValue] = specStr.split(':')
          if (specName && specValue) {
            if (!specMap.has(specName)) {
              specMap.set(specName, new Set())
            }
            specMap.get(specName)!.add(specValue)
          }
        })
      }
    })

    formData.value.specifications = Array.from(specMap.entries()).map(([name, values]) => ({
      name,
      values: Array.from(values),
      inputVisible: false,
      inputValue: ''
    }))

    skuList.value = props.commodity.specification_list.map((sku: any) => ({
      specs: Array.isArray(sku.specs) ? [...sku.specs] : [],
      price: Number(sku.price) || 0,
      stock: Number(sku.stock) || 0
    }))
  } else {
    formData.value.specifications = []
    skuList.value = []
  }
}

onMounted(async () => {
  try {
    const response = await Axios.get('/buter_get_classify', {
      params: {
        store_id: id.value
      },
      headers: {
        'access-token': token.value
      }
    })
    if (response.data.current) {
      classifyList.value = []
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

  if (props.commodity) {
    nextTick(() => {
      initFormData()
    })
  }
})

watch(() => props.commodity, (newVal, oldVal) => {
  if (newVal) {
    nextTick(() => {
      initFormData()
    })
  } else if (oldVal && !newVal) {
    resetFormData()
  }
}, { deep: true, immediate: true })

const handleImageChange = (uploadFile: any) => {
  const fileName = uploadFile.name || ''
  const lastDotIndex = fileName.lastIndexOf('.')
  
  if (lastDotIndex <= 0 || lastDotIndex >= fileName.length - 1) {
    ElMessage.error('文件格式不正确，请上传图片文件！')
    return false
  }
  
  const fileExtension = fileName.substring(lastDotIndex + 1).toLowerCase()
  
  if (!file_name.includes(fileExtension)) {
    ElMessage.error(`不支持的图片格式！支持的格式：${file_name.join(', ').toUpperCase()}`)
    return false
  }

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

const handleImageExceed = () => {
  ElMessage.warning('最多只能上传5张图片!')
}

const handleImageRemove = (file: any) => {
  if (file.url && file.url.startsWith('blob:')) {
    URL.revokeObjectURL(file.url)
  }
}

const handleImagePreview = (file: any) => {
  if (file.url) {
    previewImageUrl.value = file.url
  } else if (file.raw instanceof File) {
    previewImageUrl.value = URL.createObjectURL(file.raw)
  }
  previewDialogVisible.value = true
}

const closePreview = () => {
  previewDialogVisible.value = false
  previewImageUrl.value = ''
}

const cleanupPreview = () => {
  if (previewImageUrl.value && previewImageUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewImageUrl.value)
  }
  previewImageUrl.value = ''
}

const handleCancel = () => {
  emit('cancel')
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      submitLoading.value = true
      const commitFormData = new FormData()
      commitFormData.append('token', token.value || '')
      commitFormData.append('stroe_id', id.value.toString())
      commitFormData.append('shopping_id', props.commodity?.id.toString() || '')
      commitFormData.append('name', formData.value.name)

      formData.value.tags.forEach((tag: string) => {
        commitFormData.append('type', tag)
      })

      const imageFiles: File[] = []
      
      for (const file of formData.value.image) {
        if (file.raw) {
          imageFiles.push(file.raw)
        } else if (file.isExisting && file.base64) {
          try {
            const base64Data = file.base64
            const byteCharacters = atob(base64Data)
            const byteNumbers = new Array(byteCharacters.length)
            for (let i = 0; i < byteCharacters.length; i++) {
              byteNumbers[i] = byteCharacters.charCodeAt(i)
            }
            const byteArray = new Uint8Array(byteNumbers)
            const blob = new Blob([byteArray], { type: 'image/jpeg' })
            const imageFile = new File([blob], file.name || `image-${imageFiles.length}.jpg`, { type: 'image/jpeg' })
            imageFiles.push(imageFile)
          } catch (error) {
            console.error('转换base64图片失败:', error)
            ElMessage.warning(`图片 ${file.name} 转换失败，将跳过`)
          }
        }
      }
      
      if (imageFiles.length === 0) {
        ElMessage.error('请至少保留或上传一张商品图片！')
        submitLoading.value = false
        return false
      }
      
      imageFiles.forEach((file) => {
        commitFormData.append('img_list', file)
      })

      const validSpecs = formData.value.specifications.filter(spec => 
        spec.name.trim() && spec.values.length > 0
      )
      
      if (validSpecs.length === 0) {
        ElMessage.error('请至少添加一个商品规格，并为每个规格添加至少一个值！')
        submitLoading.value = false
        return false
      }

      if (skuList.value.length === 0) {
        ElMessage.error('规格组合生成失败，请检查规格设置！')
        submitLoading.value = false
        return false
      }
      
      const invalidSku = skuList.value.find(sku => sku.price <= 0 || sku.stock < 0)
      if (invalidSku) {
        ElMessage.error('请为所有规格组合设置有效的价格（>0）和库存（≥0）！')
        submitLoading.value = false
        return false
      }

      commitFormData.append('sku_list', JSON.stringify(skuList.value))
      commitFormData.append('classify_categorize', formData.value.category_id.toString())
      commitFormData.append('info', formData.value.description)

      try {
        const res = await Axios.patch('/buyer_commodity_edit', commitFormData, {
          headers: {
            'access-token': token.value,
            'Content-Type': 'multipart/form-data'
          }
        })
        if (res.status == 200) {
          if (res.data.current || res.data.success) {
            ElMessage.success(res.data.msg || '商品修改成功！')
            emit('success')
            submitLoading.value = false
            return true
          } else {
            ElMessage.error(res.data.msg || '商品修改失败！')
            submitLoading.value = false
            return false
          }
        } else {
          ElMessage.error('商品修改失败！')
          submitLoading.value = false
          return false
        }
      } catch (error: any) {
        console.error('商品修改失败:', error)
        const errorMsg = error.response?.data?.msg || error.message || '商品修改失败，请稍后重试'
        ElMessage.error(errorMsg)
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
  nextTick(() => {
    formRef.value?.validateField('specifications')
  })
}

const showSpecValueInput = (specIndex: number) => {
  formData.value.specifications[specIndex].inputVisible = true
  nextTick(() => {
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
  nextTick(() => {
    formRef.value?.validateField('specifications')
  })
}

const handleSpecNameBlur = () => {
  generateSkuCombinations()
  nextTick(() => {
    formRef.value?.validateField('specifications')
  })
}

const generateSkuCombinations = () => {
  const specs = formData.value.specifications.filter(spec => 
    spec.name.trim() && spec.values.length > 0
  )
  
  if (specs.length === 0) {
    skuList.value = []
    return
  }

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

onUnmounted(() => {
  cleanupPreview()
})

</script>

<style scoped>
.commodity-edit-container {
  padding: 20px;
}

.commodity-form {
  padding: 20px 0;
}

.form-section {
  padding: 20px;
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

.image-uploader {
  width: 100%;
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

.form-actions {
  margin-top: 30px;
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #409eff;
}

.form-actions .el-button {
  margin: 0 12px;
  min-width: 120px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.commodity-tag {
  margin: 0;
}

.tag-input {
  width: 120px;
}

.add-tag-btn {
  border-style: dashed;
}

.tag-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.specifications-container {
  width: 100%;
}

.spec-item {
  margin-bottom: 20px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
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

.preview-dialog-content {
  text-align: center;
  padding: 20px;
}

.preview-image-large {
  max-width: 100%;
  max-height: 70vh;
  border-radius: 8px;
}

.preview-dialog-footer {
  text-align: center;
  padding: 16px 0;
}
</style>
