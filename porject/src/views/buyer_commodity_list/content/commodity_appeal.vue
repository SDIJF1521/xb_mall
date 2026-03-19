<template>
  <div class="appeal-container">
    <!-- 违规信息 -->
    <el-card shadow="never" class="violation-info-card">
      <template #header>
        <div class="card-header">
          <el-icon color="#F56C6C"><WarningFilled /></el-icon>
          <span>违规信息</span>
        </div>
      </template>
      <el-descriptions :column="1" border size="default">
        <el-descriptions-item label="商品名称">{{ commodity?.name }}</el-descriptions-item>
        <el-descriptions-item label="商品ID">{{ commodity?.id }}</el-descriptions-item>
        <el-descriptions-item label="违规原因">
          <el-text type="danger">{{ violationReason || '加载中...' }}</el-text>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 申诉状态 -->
    <el-card v-if="appealData" shadow="never" class="appeal-status-card">
      <template #header>
        <div class="card-header">
          <el-icon :color="appealData.status === 'pending' ? '#E6A23C' : appealData.status === 'approved' ? '#67C23A' : '#F56C6C'">
            <Clock v-if="appealData.status === 'pending'" />
            <CircleCheckFilled v-else-if="appealData.status === 'approved'" />
            <CircleCloseFilled v-else />
          </el-icon>
          <span>申诉记录</span>
        </div>
      </template>
      <el-descriptions :column="1" border size="default">
        <el-descriptions-item label="申诉状态">
          <el-tag :type="appealData.status === 'pending' ? 'warning' : appealData.status === 'approved' ? 'success' : 'danger'">
            {{ appealData.status_text }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="申诉理由">{{ appealData.reason }}</el-descriptions-item>
        <el-descriptions-item label="申诉时间">{{ appealData.appeal_time }}</el-descriptions-item>
        <el-descriptions-item v-if="appealData.handle_time" label="处理时间">{{ appealData.handle_time }}</el-descriptions-item>
        <el-descriptions-item v-if="appealData.remark" label="处理备注">
          <el-text :type="appealData.status === 'approved' ? 'success' : 'danger'">{{ appealData.remark }}</el-text>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 提交申诉表单（无待处理申诉时显示） -->
    <el-card v-if="!hasPendingAppeal" shadow="never" class="appeal-form-card">
      <template #header>
        <div class="card-header">
          <el-icon color="#409EFF"><EditPen /></el-icon>
          <span>提交申诉</span>
        </div>
      </template>
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="80px">
        <el-form-item label="申诉理由" prop="reason">
          <el-input
            v-model="formData.reason"
            type="textarea"
            :rows="5"
            placeholder="请详细描述您的申诉理由，说明商品不违规的原因..."
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item>
          <div class="form-actions">
            <el-button @click="handleCancel" size="large">取消</el-button>
            <el-button type="primary" @click="handleSubmit" :loading="submitLoading" size="large">
              提交申诉
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 有待处理申诉时显示提示 -->
    <el-alert
      v-if="hasPendingAppeal"
      title="您已提交申诉，请耐心等待平台审核"
      type="warning"
      :closable="false"
      show-icon
      class="pending-alert"
    />

    <div v-if="hasPendingAppeal" class="bottom-actions">
      <el-button @click="handleCancel" size="large">关闭</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { WarningFilled, Clock, CircleCheckFilled, CircleCloseFilled, EditPen } from '@element-plus/icons-vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

defineOptions({
  name: 'CommodityAppeal',
})

interface Commodity {
  id: number
  name: string
  audit: number
  [key: string]: any
}

const props = defineProps<{
  commodity: Commodity | null
}>()

const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'success'): void
}>()

const route = useRoute()
const id = ref(route.params.id)
const token = ref(localStorage.getItem('buyer_access_token') || '')

const Axios = axios.create({
  baseURL: "http://127.0.0.1:8000/api"
})

const formRef = ref()
const submitLoading = ref(false)
const violationReason = ref('')
const appealData = ref<any>(null)
const hasPendingAppeal = ref(false)

const formData = ref({
  reason: ''
})

const rules = ref({
  reason: [
    { required: true, message: '请输入申诉理由', trigger: 'blur' },
    { min: 10, max: 500, message: '申诉理由长度应在 10 到 500 个字符之间', trigger: 'blur' }
  ]
})

async function getAppealStatus() {
  if (!props.commodity) return
  try {
    const res = await Axios.get('/buyer_commodity_appeal_status', {
      params: {
        stroe_id: id.value,
        shopping_id: props.commodity.id
      },
      headers: {
        'access-token': token.value
      }
    })
    if (res.data.current) {
      if (res.data.violation_reason) {
        violationReason.value = res.data.violation_reason
      }
      if (res.data.has_appeal) {
        appealData.value = res.data.data
        hasPendingAppeal.value = res.data.data.status === 'pending'
      }
    }
  } catch (error) {
    console.error('获取申诉状态失败:', error)
  }
}

function handleCancel() {
  emit('cancel')
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      submitLoading.value = true
      try {
        const postData = new FormData()
        postData.append('token', token.value)
        postData.append('stroe_id', id.value as string)
        postData.append('shopping_id', props.commodity?.id.toString() || '')
        postData.append('reason', formData.value.reason)

        const res = await Axios.post('/buyer_commodity_violation_appeal', postData, {
          headers: {
            'access-token': token.value,
            'Content-Type': 'multipart/form-data'
          }
        })
        if (res.data.current || res.data.code === 200) {
          ElMessage.success(res.data.msg || '申诉已提交')
          emit('success')
        } else {
          ElMessage.error(res.data.msg || '申诉提交失败')
        }
      } catch (error: any) {
        ElMessage.error(error.response?.data?.msg || '申诉提交失败，请稍后重试')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

onMounted(() => {
  getAppealStatus()
})
</script>

<style scoped>
.appeal-container {
  padding: 10px 0;
}

.violation-info-card,
.appeal-status-card,
.appeal-form-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  width: 100%;
}

.pending-alert {
  margin-top: 16px;
}

.bottom-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
