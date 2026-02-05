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
          <el-checkbox label="stockStatus">库存状态</el-checkbox>
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
import axios from 'axios';

const props = defineProps<{
  modelValue: boolean;
  currentData?: any[];
  selectedData?: any[];
  storeId?: string | number;
  token?: string;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  exportSuccess: [];
  exportError: [];
}>();

const dialogVisible = ref(props.modelValue);
const exportLoading = ref(false);

// 创建axios实例
const axiosInstance = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  timeout: 30000, // 导出全部数据可能需要更长时间
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded'
  }
});

const formData = reactive({
  exportScope: 'current' as 'current' | 'selected' | 'all',
  fileName: `库存数据_${new Date().toISOString().slice(0, 10)}.csv`,
  selectedFields: ['id', 'name', 'specification', 'currentStock', 'minStock', 'maxStock', 'stockStatus'] as string[],
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
      case 'stockStatus': return '库存状态';
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

const ensureStockStatus = (data: any[]): any[] => {
  return data.map(item => ({
    ...item,
    stockStatus: item.stockStatus || (() => {
      if (item.currentStock <= 0) return '缺货';
      if (item.currentStock <= item.minStock) return '库存不足';
      if (item.currentStock <= item.minStock * 2) return '库存较低';
      return '库存充足';
    })()
  }));
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
      exportData = ensureStockStatus([...props.currentData]);
    } else if (formData.exportScope === 'selected' && props.selectedData) {
      exportData = ensureStockStatus([...props.selectedData]);
    } else if (formData.exportScope === 'all') {
      if (!props.storeId || !props.token) {
        ElMessage.error('缺少必要的参数');
        return;
      }

      try {
        const params = new URLSearchParams({
          stroe_id: String(Array.isArray(props.storeId) ? props.storeId[0] : props.storeId),
          token: props.token
        });

        const response = await axiosInstance.post('/buyer_commodity_repertory_all', params);

        if (response.data.success && response.data.data) {
          exportData = [];
          response.data.data.forEach((item: any) => {
            if (item.specifications && item.specifications.length > 0) {
              item.specifications.forEach((spec: any) => {
                exportData.push({
                id: `${item.shopping_id}`,
                name: item.name,
                specification: spec.specification_id.toString(),
                currentStock: spec.stock || 0,
                minStock: spec.minimum_balance || 0,
                maxStock: spec.maximum_inventory || 0,
                stockStatus: spec.stock_status || '',
                lastUpdated: spec.time || item.time
              });
              });
            } else {
              exportData.push({
                id: item.shopping_id,
                name: item.name,
                specification: '无规格',
                currentStock: 0,
                minStock: 0,
                maxStock: 0,
                stockStatus: '缺货',
                lastUpdated: item.time
              });
            }
          });
        } else {
          ElMessage.error(response.data.msg || '获取全部数据失败');
          exportData = props.currentData ? [...props.currentData] : [];
        }
      } catch (error) {
        console.error('获取全部数据失败:', error);
        ElMessage.error('获取全部数据失败，将使用当前页面数据');
        exportData = props.currentData ? [...props.currentData] : [];
      }
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
