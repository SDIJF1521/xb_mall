<template>
    <div class="reject-audit-container">
        <div class="reject-header">
            <el-icon class="header-icon"><Warning /></el-icon>
            <h3 class="header-title">审核拒绝</h3>
        </div>

        <el-form :model="form" label-width="100px" class="reject-form">
            <el-form-item
                label="拒绝理由"
                prop="reason"
                :rules="[{ required: true, message: '请填写拒绝理由', trigger: 'blur' }]"
            >
                <el-input
                    v-model="form.reason"
                    type="textarea"
                    :autosize="{ minRows: 4, maxRows: 8 }"
                    placeholder="请详细说明拒绝审核的原因..."
                    class="reason-input"
                    show-word-limit
                    :maxlength="500"
                />
            </el-form-item>

            <div class="form-tips">
                <el-alert
                    title="温馨提示"
                    description="拒绝审核后，该商品将无法通过审核，请谨慎操作。"
                    type="warning"
                    :closable="false"
                    show-icon
                    class="tips-alert"
                />
            </div>
        </el-form>
    </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { Warning } from '@element-plus/icons-vue'
defineOptions({name:'CommodityRejectAudit'})

const emit = defineEmits<{
    reject: [reason: string]
    cancel: []
}>()

const form = ref({
    reason: ''
})

const sendReject = () => {
    console.log('子组件 sendReject 被调用，拒绝理由:', form.value.reason)
    emit('reject', form.value.reason)
}

const handleCancel = () => {
    emit('cancel')
}

// 暴露方法给父组件
defineExpose({
    sendReject,
    handleCancel
})
</script>
<style scoped>
.reject-audit-container {
    padding: 20px;
    background: var(--color-background);
    border-radius: 12px;
    border: 1px solid var(--color-border);
    transition: background-color 0.3s ease, border-color 0.3s ease;
}

.reject-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 2px solid #f56c6c;
    transition: border-color 0.3s ease;
}

.header-icon {
    font-size: 24px;
    color: #f56c6c;
    background: rgba(245, 108, 108, 0.1);
    padding: 8px;
    border-radius: 50%;
    transition: background-color 0.3s ease;
}

.header-title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: var(--color-text);
    background: linear-gradient(45deg, #f56c6c, #f78989);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    transition: color 0.3s ease;
}

.reject-form {
    .el-form-item {
        margin-bottom: 20px;
    }

    .el-form-item__label {
        font-weight: 500;
        color: var(--color-text);
        font-size: 14px;
        opacity: 0.8;
        transition: color 0.3s ease;
    }
}

.reason-input {
    .el-textarea__inner {
        border-radius: 8px;
        border: 1px solid var(--color-border);
        background: var(--color-background);
        color: var(--color-text);
        transition: all 0.3s ease;
        font-family: 'PingFang SC', 'Helvetica Neue', STHeiti, 'Microsoft Yahei', sans-serif;
        line-height: 1.6;
    }

    .el-textarea__inner:focus {
        border-color: #f56c6c;
        box-shadow: 0 0 0 2px rgba(245, 108, 108, 0.1);
    }

    .el-input__count {
        background: transparent;
        color: var(--color-text);
        opacity: 0.6;
        font-size: 12px;
        transition: color 0.3s ease;
    }
}

.form-tips {
    margin-top: 20px;
}

.tips-alert {
    border-radius: 8px;
    border: 1px solid #fdf6ec;

    .el-alert__title {
        font-weight: 500;
        color: #e6a23c;
    }

    .el-alert__description {
        color: #e6a23c;
        margin-top: 8px;
        line-height: 1.5;
    }

    .el-alert__icon {
        color: #e6a23c;
    }
}

/* 响应式设计 */
@media (max-width: 768px) {
    .reject-audit-container {
        padding: 16px;
    }

    .reject-header {
        gap: 8px;
        margin-bottom: 20px;
        padding-bottom: 12px;
    }

    .header-icon {
        font-size: 20px;
        padding: 6px;
    }

    .header-title {
        font-size: 16px;
    }

    .reject-form {
        .el-form-item__label {
            font-size: 13px;
        }
    }
}

/* 动画效果 */
.reject-audit-container {
    animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Element Plus 组件样式覆盖 */
:deep(.el-form-item__error) {
    color: #f56c6c;
    font-size: 12px;
    line-height: 1.4;
    margin-top: 4px;
}

:deep(.el-form-item.is-error .el-input__inner),
:deep(.el-form-item.is-error .el-textarea__inner) {
    border-color: #f56c6c;
}

:deep(.el-form-item.is-success .el-input__inner),
:deep(.el-form-item.is-success .el-textarea__inner) {
    border-color: #67c23a;
}

/* 暗色主题样式 */
.dark .reject-audit-container {
    background: var(--color-background);
    border-color: var(--color-border);
}

.dark .header-icon {
    background: rgba(245, 108, 108, 0.2);
}

.dark .header-title {
    color: var(--color-text);
}

.dark .reject-form .el-form-item__label {
    color: var(--color-text);
    opacity: 0.9;
}

.dark .reason-input .el-textarea__inner {
    background: var(--color-background);
    border-color: var(--color-border);
    color: var(--color-text);
}

.dark .reason-input .el-input__count {
    color: var(--color-text);
    opacity: 0.7;
}

.dark .tips-alert {
    background: rgba(230, 162, 60, 0.1);
    border-color: rgba(230, 162, 60, 0.3);

    .el-alert__title {
        color: #fbbf24;
    }

    .el-alert__description {
        color: #fbbf24;
    }

    .el-alert__icon {
        color: #fbbf24;
    }
}

.dark :deep(.el-form-item__error) {
    color: #f87171;
}

.dark :deep(.el-form-item.is-error .el-input__inner),
.dark :deep(.el-form-item.is-error .el-textarea__inner) {
    border-color: #f87171;
}

.dark :deep(.el-form-item.is-success .el-input__inner),
.dark :deep(.el-form-item.is-success .el-textarea__inner) {
    border-color: #4ade80;
}
</style>