<template>
    <div class="pass-audit-container">
        <div class="pass-header">
            <el-icon class="header-icon"><Check /></el-icon>
            <h3 class="header-title">通过审核</h3>
        </div>

        <el-form :model="form" label-width="100px" class="pass-form">
            <el-form-item
                label="审核备注"
                prop="remark"
            >
                <el-input
                    v-model="form.remark"
                    type="textarea"
                    :autosize="{ minRows: 3, maxRows: 6 }"
                    placeholder="可选：添加审核通过的备注信息..."
                    class="remark-input"
                    show-word-limit
                    :maxlength="200"
                />
            </el-form-item>

            <div class="form-tips">
                <el-alert
                    title="审核通过确认"
                    description="确认通过该商品的审核申请？审核通过后商品将正式上架。"
                    type="success"
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
import { Check } from '@element-plus/icons-vue'

defineOptions({name:'CommodityPassAudit'})

const emit = defineEmits<{
    pass: [remark?: string]
    cancel: []
}>()

const form = ref({
    remark: ''
})

const handlePass = () => {
    emit('pass', form.value.remark || undefined)
}

const handleCancel = () => {
    emit('cancel')
}

// 暴露方法给父组件
defineExpose({
    handlePass,
    handleCancel
})
</script>
<style scoped>
.pass-audit-container {
    padding: 20px;
    background: var(--color-background);
    border-radius: 12px;
    border: 1px solid var(--color-border);
    transition: background-color 0.3s ease, border-color 0.3s ease;
}

.pass-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 2px solid #67c23a;
    transition: border-color 0.3s ease;
}

.header-icon {
    font-size: 24px;
    color: #67c23a;
    background: rgba(103, 194, 58, 0.1);
    padding: 8px;
    border-radius: 50%;
    transition: background-color 0.3s ease;
}

.header-title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: var(--color-text);
    background: linear-gradient(45deg, #67c23a, #95d475);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    transition: color 0.3s ease;
}

.pass-form {
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

.remark-input {
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
        border-color: #67c23a;
        box-shadow: 0 0 0 2px rgba(103, 194, 58, 0.1);
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
    border: 1px solid #f0f9ff;

    .el-alert__title {
        font-weight: 500;
        color: #52c41a;
    }

    .el-alert__description {
        color: #52c41a;
        margin-top: 8px;
        line-height: 1.5;
    }

    .el-alert__icon {
        color: #52c41a;
    }
}

/* 响应式设计 */
@media (max-width: 768px) {
    .pass-audit-container {
        padding: 16px;
    }

    .pass-header {
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

    .pass-form {
        .el-form-item__label {
            font-size: 13px;
        }
    }
}

/* 动画效果 */
.pass-audit-container {
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
.dark .pass-audit-container {
    background: var(--color-background);
    border-color: var(--color-border);
}

.dark .header-icon {
    background: rgba(103, 194, 58, 0.2);
}

.dark .header-title {
    color: var(--color-text);
}

.dark .pass-form .el-form-item__label {
    color: var(--color-text);
    opacity: 0.9;
}

.dark .remark-input .el-textarea__inner {
    background: var(--color-background);
    border-color: var(--color-border);
    color: var(--color-text);
}

.dark .remark-input .el-input__count {
    color: var(--color-text);
    opacity: 0.7;
}

.dark .tips-alert {
    background: rgba(82, 196, 26, 0.1);
    border-color: rgba(82, 196, 26, 0.3);

    .el-alert__title {
        color: #73d13d;
    }

    .el-alert__description {
        color: #73d13d;
    }

    .el-alert__icon {
        color: #73d13d;
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