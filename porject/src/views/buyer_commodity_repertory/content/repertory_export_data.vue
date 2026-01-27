<template>
  <el-dialog
    v-model="dialogVisible"
    title="导出库存数据"
    width="600px"
    append-to-body
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form :model="formData" label-width="120px">
      <el-form-item label="导出范围">
        <el-radio-group v-model="formData.exportScope">
          <el-radio label="current">当前页面数据</el-radio>
          <el-radio label="selected">已选中数据</el-radio>
          <el-radio label="all">全部数据</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="文件名">
        <el-input
          v-model="formData.fileName"
          placeholder="请输入导出文件名"
          maxlength="50"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="包含字段">
        <el-checkbox-group v-model="formData.selectedFields">
          <el-checkbox label="id">商品ID</el-checkbox>
          <el-checkbox label="name">商品名称</el-checkbox>
          <el-checkbox label="specification">规格</el-checkbox>
          <el-checkbox label="currentStock">当前库存</el-checkbox>
          <el-checkbox label="minStock">最低库存</el-checkbox>
          <el-checkbox label="maxStock">最高库存</el-checkbox>
          <el-checkbox label="lastUpdated">更新时间</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          @click="handleExport"
          :loading="exportLoading"
          :disabled="!formData.selectedFields.length"
        >
          确定导出
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue';
import { ElMessage } from 'element-plus';

const props = defineProps<{
  modelValue: boolean;
  currentData?: any[];
  selectedData?: any[];
}>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  exportSuccess: [];
  exportError: [];
}>();

const dialogVisible = ref(props.modelValue);
const exportLoading = ref(false);

const formData = reactive({
  exportScope: 'current' as 'current' | 'selected' | 'all',
  fileName: `库存数据_${new Date().toISOString().slice(0, 10)}.csv`,
  selectedFields: ['id', 'name', 'specification', 'currentStock', 'minStock', 'maxStock'] as string[],
});

watch(() => props.modelValue, (newValue) => {
  dialogVisible.value = newValue;
});

watch(dialogVisible, (newValue) => {
  emit('update:modelValue', newValue);
});

const handleClose = () => {
  dialogVisible.value = false;
};

const exportToCSV = (data: any[], fields: string[], filename: string) => {
  if (!data || data.length === 0) {
    ElMessage.warning('没有数据可导出');
    return;
  }

  const headers = fields.map(field => {
    switch(field) {
      case 'id': return '商品ID';
      case 'name': return '商品名称';
      case 'specification': return '规格';
      case 'currentStock': return '当前库存';
      case 'minStock': return '最低库存';
      case 'maxStock': return '最高库存';
      case 'lastUpdated': return '更新时间';
      default: return field;
    }
  });

  const csvContent = [
    headers.join(','),
    ...data.map(item =>
      fields.map(field => {
        let value = item[field];
        if (typeof value === 'string' && (value.includes(',') || value.includes('\n') || value.includes('"'))) {
          value = `"${value.replace(/"/g, '""')}"`;
        }
        return value !== undefined && value !== null ? value : '';
      }).join(',')
    )
  ].join('\n');

  const blob = new Blob(['\ufeff', csvContent], { type: 'text/csv;charset=utf-8;' });

  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);

  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const handleExport = async () => {
  if (!formData.selectedFields.length) {
    ElMessage.warning('请至少选择一个导出字段');
    return;
  }

  exportLoading.value = true;

  try {
    let exportData: any[] = [];

    if (formData.exportScope === 'current' && props.currentData) {
      exportData = [...props.currentData];
    } else if (formData.exportScope === 'selected' && props.selectedData) {
      exportData = [...props.selectedData];
    } else if (formData.exportScope === 'all') {
      ElMessage.warning('导出全部数据功能开发中...');
      exportData = props.currentData ? [...props.currentData] : [];
    } else {
      exportData = props.currentData ? [...props.currentData] : [];
    }

    if (!exportData.length) {
      ElMessage.warning('没有数据可导出');
      return;
    }

    exportToCSV(exportData, formData.selectedFields, formData.fileName);

    ElMessage.success('导出成功');
    emit('exportSuccess');
    handleClose();
  } catch (error) {
    console.error('导出失败:', error);
    ElMessage.error('导出失败，请重试');
    emit('exportError');
  } finally {
    exportLoading.value = false;
  }
};
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
