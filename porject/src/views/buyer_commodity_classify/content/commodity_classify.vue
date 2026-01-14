<template>
  <div class="classify-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">商品分类管理</h2>
      <p class="page-subtitle">管理您的商品分类，优化商品展示结构</p>
    </div>

    <!-- 页面头部操作区 -->
    <div class="header-actions">
      <div class="search-section">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索分类名称"
          clearable
          size="large"
          class="search-input"
          @input="handleSearch"
          @clear="handleSearchClear"
        >
          <template #prefix>
            <el-icon class="search-icon"><Search /></el-icon>
          </template>
        </el-input>
      </div>
      <el-button 
        type="primary" 
        size="large" 
        @click="handleAdd"
        class="add-button"
      >
        <el-icon><Plus /></el-icon>
        添加分类
      </el-button>
    </div>

    <!-- 分类列表 -->
    <div class="classify-list">
      <el-card 
        v-for="(item, index) in filteredClassifyList" 
        :key="item.id || index"
        class="classify-card"
        :class="`card-${(index % 4) + 1}`"
        shadow="hover"
      >
        <template #header>
          <div class="card-header">
            <div class="classify-info">
              <el-icon class="classify-icon" size="24">
                <Folder />
              </el-icon>
              <div class="name-wrapper">
                <span class="classify-name">{{ item.name }}</span>
                <span class="classify-id">ID: {{ item.id }}</span>
              </div>
            </div>
            <div class="card-actions">
              <el-button 
                type="primary" 
                size="small" 
                :icon="Edit"
                circle
                @click="handleEdit(item)"
                title="编辑"
                class="action-btn"
              />
              <el-button 
                type="danger" 
                size="small" 
                :icon="Delete"
                circle
                @click="handleDelete(item)"
                title="删除"
                class="action-btn"
              />
            </div>
          </div>
        </template>
        <div class="card-content">
          <div class="classify-details">
            <div class="detail-item">
              <span class="label">分类ID：</span>
              <span class="value">{{ item.id }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 空状态 -->
      <el-empty 
        v-if="filteredClassifyList.length === 0" 
        description="暂无分类数据"
        :image-size="120"
      >
        <el-button type="primary" @click="handleAdd">添加第一个分类</el-button>
      </el-empty>
    </div>

    <!-- 添加/编辑分类对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
    append-to-body
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        label-position="left"
      >
        <el-form-item label="分类名称" prop="name">
          <el-input
            v-model="formData.name"
            placeholder="请输入分类名称"
            maxlength="20"
            show-word-limit
            clearable
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCancel">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 删除确认对话框 -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="删除分类"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="delete-content">
        <el-icon class="warning-icon" size="48"><WarningFilled /></el-icon>
        <p class="delete-message">
          确定要删除分类 <strong>"{{ currentClassify?.name }}"</strong> 吗？
        </p>
        <p class="delete-tip">删除后该分类下的商品将无法通过分类查找</p>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="deleteDialogVisible = false">取消</el-button>
          <el-button type="danger" :loading="deleteLoading" @click="confirmDelete">
            确定删除
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Search, 
  Plus, 
  Edit, 
  Delete, 
  Folder,
  WarningFilled
} from '@element-plus/icons-vue'

defineOptions({
  name: 'CommodityClassify'
})

interface ClassifyItem {
  id: number | string
  name: string
}

const searchKeyword = ref('')
const classifyList = ref<ClassifyItem[]>([])
const dialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const submitLoading = ref(false)
const deleteLoading = ref(false)
const currentClassify = ref<ClassifyItem | null>(null)
const isEditMode = ref(false)
const formRef = ref()

const formData = ref({
  name: ''
})

const formRules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
    { min: 2, max: 20, message: '分类名称长度在 2 到 20 个字符', trigger: 'blur' }
  ]
}

const dialogTitle = computed(() => {
  return isEditMode.value ? '编辑分类' : '添加分类'
})

const filteredClassifyList = computed(() => {
  if (!searchKeyword.value.trim()) {
    return classifyList.value
  }
  const keyword = searchKeyword.value.toLowerCase()
  return classifyList.value.filter(item => 
    item.name.toLowerCase().includes(keyword)
  )
})

const handleSearch = () => {
}

const handleSearchClear = () => {
  searchKeyword.value = ''
}

const handleAdd = () => {
  isEditMode.value = false
  formData.value = {
    name: ''
  }
  dialogVisible.value = true
}

const handleEdit = (item: ClassifyItem) => {
  isEditMode.value = true
  currentClassify.value = item
  formData.value = {
    name: item.name
  }
  dialogVisible.value = true
}

const handleDelete = (item: ClassifyItem) => {
  currentClassify.value = item
  deleteDialogVisible.value = true
}

const handleCancel = () => {
  dialogVisible.value = false
  formRef.value?.resetFields()
  currentClassify.value = null
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      submitLoading.value = true
      try {
        // TODO: 调用API保存分类
        // 这里先模拟成功
        await new Promise(resolve => setTimeout(resolve, 500))
        
        if (isEditMode.value) {
          const index = classifyList.value.findIndex(item => item.id === currentClassify.value?.id)
          if (index !== -1) {
            classifyList.value[index] = {
              ...classifyList.value[index],
              name: formData.value.name
            }
          }
          ElMessage.success('分类更新成功')
        } else {
          const newItem: ClassifyItem = {
            id: Date.now(),
            name: formData.value.name
          }
          classifyList.value.push(newItem)
          ElMessage.success('分类添加成功')
        }
        
        dialogVisible.value = false
        formRef.value?.resetFields()
        currentClassify.value = null
      } catch (error) {
        ElMessage.error('操作失败，请稍后重试')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const confirmDelete = async () => {
  if (!currentClassify.value) return
  
  deleteLoading.value = true
  try {
    // TODO: 调用API删除分类
    // 这里先模拟成功
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const index = classifyList.value.findIndex(item => item.id === currentClassify.value?.id)
    if (index !== -1) {
      classifyList.value.splice(index, 1)
    }
    
    ElMessage.success('分类删除成功')
    deleteDialogVisible.value = false
    currentClassify.value = null
  } catch (error) {
    ElMessage.error('删除失败，请稍后重试')
  } finally {
    deleteLoading.value = false
  }
}

onMounted(() => {
  // TODO: 从API加载分类列表
  // 这里先使用模拟数据
  classifyList.value = [
    {
      id: 1,
      name: '电子产品'
    },
    {
      id: 2,
      name: '服装配饰'
    },
    {
      id: 3,
      name: '食品饮料'
    },
    {
      id: 4,
      name: '家居用品'
    }
  ]
})
</script>

<style scoped>
.classify-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-title {
  font-size: 32px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
}

.page-subtitle {
  font-size: 16px;
  color: #7f8c8d;
  margin: 0;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  gap: 16px;
  flex-wrap: wrap;
}

.search-section {
  flex: 1;
  min-width: 300px;
}

.search-input {
  max-width: 400px;
}

.search-icon {
  color: #409eff;
}

.add-button {
  display: flex;
  align-items: center;
  gap: 6px;
}

.classify-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.classify-card {
  transition: all 0.3s ease;
  border-radius: 12px;
}

.classify-card.card-1 {
  border-left: 4px solid #409eff;
}

.classify-card.card-2 {
  border-left: 4px solid #67c23a;
}

.classify-card.card-3 {
  border-left: 4px solid #e6a23c;
}

.classify-card.card-4 {
  border-left: 4px solid #909399;
}

.classify-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
}

.classify-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.classify-icon {
  color: #409eff;
  transition: all 0.3s ease;
}

.classify-card.card-1 .classify-icon {
  color: #409eff;
}

.classify-card.card-2 .classify-icon {
  color: #67c23a;
}

.classify-card.card-3 .classify-icon {
  color: #e6a23c;
}

.classify-card.card-4 .classify-icon {
  color: #909399;
}

.name-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.classify-name {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  line-height: 1.4;
}

.classify-id {
  font-size: 13px;
  color: #909399;
  font-weight: 400;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  transition: all 0.3s ease;
}

.action-btn:hover {
  transform: scale(1.1);
}

.card-content {
  padding: 8px 0;
}

.classify-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-item {
  display: flex;
  align-items: center;
  font-size: 14px;
}

.detail-item .label {
  color: #909399;
  min-width: 80px;
  font-weight: 500;
}

.detail-item .value {
  color: #606266;
  flex: 1;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}


.delete-content {
  text-align: center;
  padding: 20px 0;
}

.warning-icon {
  color: #e6a23c;
  margin-bottom: 16px;
}

.delete-message {
  font-size: 16px;
  color: #303133;
  margin: 12px 0;
  line-height: 1.6;
}

.delete-message strong {
  color: #409eff;
}

.delete-tip {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

@media (max-width: 768px) {
  .classify-container {
    padding: 15px;
  }

  .page-title {
    font-size: 28px;
  }

  .page-subtitle {
    font-size: 14px;
    margin-bottom: 30px;
  }

  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .search-section {
    min-width: 100%;
  }

  .search-input {
    max-width: 100%;
  }

  .add-button {
    width: 100%;
    justify-content: center;
  }

  .classify-list {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .card-actions {
    width: 100%;
    justify-content: flex-end;
  }
}

@media (max-width: 480px) {
  .classify-container {
    padding: 12px;
  }

  .classify-name {
    font-size: 16px;
  }

  .classify-icon {
    font-size: 20px !important;
  }
}
</style>
