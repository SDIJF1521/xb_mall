<template>
  <div class="putaway-dialog-container">
    <!-- 成功图标和提示内容 -->
    <div class="putaway-content">
      <div class="success-icon-wrapper">
        <el-icon class="success-icon" :size="64">
          <CircleCheckFilled />
        </el-icon>
      </div>
      <h3 class="putaway-title">确认上架该商品吗？</h3>
      <p class="putaway-message">上架后商品将重新对外展示，用户可以正常购买</p>
    </div>

    <!-- 操作按钮 -->
    <div class="putaway-actions">
      <el-button
        type="info"
        size="large"
        :disabled="loading"
        @click="handleCancel"
        class="cancel-btn"
      >
        <el-icon><Close /></el-icon>
        取消
      </el-button>
      <el-button
        type="success"
        size="large"
        :loading="loading"
        @click="handleConfirm"
        class="confirm-btn"
      >
        <el-icon v-if="!loading"><Top /></el-icon>
        确认上架
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { CircleCheckFilled, Top, Close } from '@element-plus/icons-vue'
import axios from 'axios'

defineOptions({
  name: 'BuyerCommodityPutaway'
})

interface Props {
  commodityId?: number | string
}

const props = withDefaults(defineProps<Props>(), {
  commodityId: undefined
})

const emit = defineEmits<{
  cancel: []
  success: []
}>()

const token = localStorage.getItem('buyer_access_token') || ''
const Axios = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
})

const route = useRoute()
const id = ref(route.params.id)
const loading = ref(false)

const handleCancel = () => {
  emit('cancel')
}

const handleConfirm = async () => {
  try {
    loading.value = true

    const formdata = new FormData()
    formdata.append('token', token || '')
    formdata.append('stroe_id', id.value.toString())
    formdata.append('shopping_id', props.commodityId?.toString() || '0')

    const res = await Axios.post('/buyer_commodity_putaway', formdata)

    if (res.status == 200) {
      if (res.data.current) {
        ElMessage.success(res.data.msg || '商品上架成功')
        emit('success')
      } else {
        ElMessage.error(res.data.msg || '商品上架失败')
      }
    } else {
      ElMessage.error('商品上架失败')
    }
  } catch (error: any) {
    console.error('上架商品失败:', error)
    ElMessage.error(error.response?.data?.msg || '上架失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.putaway-dialog-container {
  padding: 20px 0;
  min-width: 400px;
}

.putaway-content {
  text-align: center;
  padding: 20px 0 30px;
}

.success-icon-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.success-icon {
  color: #67c23a;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.9;
  }
}

.putaway-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px 0;
  line-height: 1.5;
}

.putaway-message {
  font-size: 14px;
  color: #909399;
  margin: 0;
  line-height: 1.6;
  padding: 0 20px;
}

.putaway-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.putaway-actions .el-button {
  min-width: 120px;
  height: 40px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.cancel-btn {
  background: #f5f7fa;
  border-color: #dcdfe6;
  color: #606266;
}

.cancel-btn:hover {
  background: #ecf5ff;
  border-color: #b3d8ff;
  color: #409eff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.confirm-btn {
  background: linear-gradient(135deg, #67c23a 0%, #529b2e 100%);
  border: none;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.3);
}

.confirm-btn:hover {
  background: linear-gradient(135deg, #529b2e 0%, #3d7a22 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(103, 194, 58, 0.4);
}

.confirm-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.3);
}

.confirm-btn.is-loading {
  background: linear-gradient(135deg, #67c23a 0%, #529b2e 100%);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .putaway-dialog-container {
    min-width: auto;
    padding: 15px 0;
  }

  .putaway-content {
    padding: 15px 0 20px;
  }

  .success-icon {
    font-size: 48px;
  }

  .putaway-title {
    font-size: 18px;
  }

  .putaway-message {
    font-size: 13px;
    padding: 0 10px;
  }

  .putaway-actions {
    flex-direction: column;
    gap: 12px;
  }

  .putaway-actions .el-button {
    width: 100%;
    min-width: auto;
  }
}
</style>
