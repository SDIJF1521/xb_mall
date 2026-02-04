<template>
  <div class="commodity-repertory-container">
    <!-- 库存统计卡片 -->
    <el-row :gutter="20" class="statistics-row">
      <el-col :span="6">
        <el-card class="statistics-card">
          <div class="statistics-item">
            <div class="statistics-icon warning">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="statistics-content">
              <div class="statistics-value">{{ lowStockCount }}</div>
              <div class="statistics-label">库存不足</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="statistics-card">
          <div class="statistics-item">
            <div class="statistics-icon success">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="statistics-content">
              <div class="statistics-value">{{ normalStockCount }}</div>
              <div class="statistics-label">库存正常</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="statistics-card">
          <div class="statistics-item">
            <div class="statistics-icon info">
              <el-icon><Document /></el-icon>
            </div>
            <div class="statistics-content">
              <div class="statistics-value">{{ totalStockCount }}</div>
              <div class="statistics-label">总库存量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="statistics-card">
          <div class="statistics-item">
            <div class="statistics-icon primary">
              <el-icon><Goods /></el-icon>
            </div>
            <div class="statistics-content">
              <div class="statistics-value">{{ totalProducts }}</div>
              <div class="statistics-label">商品种类</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索和操作栏 -->
    <el-card class="search-card">
      <el-row :gutter="20" align="middle">
        <el-col :span="8">
          <el-input
            v-model="searchKeyword"
            placeholder="请输入商品名称或ID"
            clearable
            @clear="handleSearch"
            @input="handleSearchInput"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="stockStatus" placeholder="库存状态" clearable @change="handleSearch">
            <el-option label="全部" value="" />
            <el-option label="库存充足" value="库存充足" />
            <el-option label="库存较低" value="库存较低" />
            <el-option label="库存不足" value="库存不足" />
            <el-option label="缺货" value="缺货" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>搜索
          </el-button>
        </el-col>
        <el-col :span="8" style="text-align: right;">
          <el-button type="success" @click="handleBatchUpdate">
            <el-icon><Edit /></el-icon>批量修改
          </el-button>
          <el-button type="warning" @click="handleExport">
            <el-icon><Download /></el-icon>导出库存
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 库存列表 -->
    <el-card class="list-card">
      <el-table
        :data="stockList"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="商品ID" width="80" />
        <el-table-column prop="name" label="商品名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="specification" label="规格" width="120" />
        <el-table-column prop="currentStock" label="当前库存" width="100" align="center">
          <template #default="scope">
            <span :class="getStockClass(scope.row.currentStock, scope.row.minStock)">
              {{ scope.row.currentStock }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="minStock" label="最低库存" width="100" align="center" />
        <el-table-column prop="maxStock" label="最高库存" width="100" align="center" />
        <el-table-column label="库存状态" width="100" align="center">
          <template #default="scope">
            <el-tag :type="getStockStatusType(scope.row.currentStock, scope.row.minStock)">
              {{ getStockStatusText(scope.row.currentStock, scope.row.minStock) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lastUpdated" label="更新时间" width="160" />
        <el-table-column label="操作" fixed="right">
          <template #default="scope">
            <el-button type="primary" size="small" @click="handleEditStock(scope.row)">
              <el-icon><Edit /></el-icon>修改库存
            </el-button>
            <el-button type="success" size="small" @click="handleStockRecord(scope.row)">
              <el-icon><Document /></el-icon>库存记录
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 修改库存对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="修改库存"
      width="600px"
      append-to-body
     :close-on-click-modal="false"

    >
      <el-form
        ref="stockFormRef"
        :model="stockForm"
        :rules="stockRules"
        label-width="100px"
      >
        <el-form-item label="商品名称">
          <el-input v-model="stockForm.name" disabled />
        </el-form-item>
        <el-form-item label="当前库存">
          <el-input v-model="stockForm.currentStock" disabled />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最低库存" prop="minStock">
              <el-input-number
                v-model="stockForm.minStock"
                :min="0"
                :max="999999"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最高库存" prop="maxStock">
              <el-input-number
                v-model="stockForm.maxStock"
                :min="1"
                :max="999999"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="库存变化" prop="changeType">
          <el-radio-group v-model="stockForm.changeType">
            <el-radio label="increase">增加库存</el-radio>
            <el-radio label="decrease">减少库存</el-radio>
            <el-radio label="set">设置库存</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="变化数量" prop="changeAmount">
          <el-input-number
            v-model="stockForm.changeAmount"
            :min="stockForm.changeType === 'set' ? 0 : 1"
            :max="stockForm.changeType === 'set' ? 999999 : 999999"
            controls-position="right"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="stockForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入库存变化的备注信息"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmitStock" :loading="submitLoading">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 库存记录对话框 -->
    <el-dialog
      v-model="recordDialogVisible"
      title="库存记录"
      width="800px"
      append-to-body
      :close-on-click-modal="false"
    >
      <el-table :data="stockRecords" v-loading="recordLoading" max-height="400">
        <el-table-column prop="createTime" label="操作时间" width="160" />
        <el-table-column prop="type" label="操作类型" width="100">
          <template #default="scope">
            <el-tag :type="getRecordTypeType(scope.row.type)">
              {{ scope.row.type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="changeAmount" label="变化数量" width="100" />
        <el-table-column prop="beforeStock" label="操作前库存" width="100" />
        <el-table-column prop="afterStock" label="操作后库存" width="100" />
        <el-table-column prop="operator" label="操作人" width="120" />
        <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
      </el-table>
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="recordCurrentPage"
          v-model:page-size="recordPageSize"
          :total="recordTotal"
          layout="total, prev, pager, next"
          @current-change="handleRecordCurrentChange"
        />
      </div>
    </el-dialog>

    <repertory-export-data
      v-model="exportDialogVisible"
      :current-data="exportCurrentData"
      :selected-data="exportSelectedData"
      @export-success="handleExportSuccess"
      @export-error="handleExportError"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { useRoute } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { Warning, CircleCheck, Goods, Search, Edit, Download, Document } from '@element-plus/icons-vue'
import RepertoryExportData from './repertory_export_data.vue'

const route = useRoute()
const storeId = ref(route.params.id)

const token = ref(localStorage.getItem('buyer_access_token') || '')

const axiosInstance = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded'
  }
})

// 数据定义
interface StockItem {
  id: number | string
  productId: number
  name: string
  specification: string
  currentStock: number
  minStock: number
  maxStock: number
  lastUpdated: string
}

interface StockRecord {
  id: number
  createTime: string
  type: string
  changeAmount: number
  beforeStock: number
  afterStock: number
  operator: string
  remark: string
}
const loading = ref(false)
const searchKeyword = ref('')
const stockStatus = ref('')
const stockList = ref<StockItem[]>([])
const selectedItems = ref<StockItem[]>([])

// 分页数据
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const lowStockCount = ref(0)
const normalStockCount = ref(0)
const totalStockCount = ref(0)
const totalProducts = ref(0)

// 对话框状态
const editDialogVisible = ref(false)
const recordDialogVisible = ref(false)
const submitLoading = ref(false)
const recordLoading = ref(false)

// 表单数据
const stockFormRef = ref<FormInstance>()
const stockForm = reactive({
  id: 0,
  name: '',
  currentStock: 0,
  minStock: 0,
  maxStock: 0,
  changeType: 'increase',
  changeAmount: 0,
  remark: '',
  specificationId: ''
})

// 表单验证规则
const stockRules: FormRules = {
  changeType: [
    { required: true, message: '请选择库存变化类型', trigger: 'change' }
  ],
  changeAmount: [
    { required: true, message: '请输入变化数量', trigger: 'blur' },
    { type: 'number', min: 1, message: '数量必须大于0', trigger: 'blur' }
  ],
  minStock: [
    { required: true, message: '请输入最低库存', trigger: 'blur' },
    { type: 'number', min: 0, message: '最低库存不能小于0', trigger: 'blur' }
  ],
  maxStock: [
    { required: true, message: '请输入最高库存', trigger: 'blur' },
    { type: 'number', min: 1, message: '最高库存必须大于0', trigger: 'blur' }
  ],
  remark: [
    { max: 200, message: '备注不能超过200个字符', trigger: 'blur' }
  ]
}

// 库存记录数据
const stockRecords = ref<StockRecord[]>([])
const recordCurrentPage = ref(1)
const recordPageSize = ref(10)
const recordTotal = ref(0)

let searchTimer: ReturnType<typeof setTimeout> | null = null
const exportDialogVisible = ref(false);
const exportCurrentData = ref<any[]>([])
const exportSelectedData = ref<any[]>([])
const handleExport = () => {
  exportCurrentData.value = [...stockList.value];
  exportSelectedData.value = [...selectedItems.value];
  exportDialogVisible.value = true;
};

const handleExportSuccess = () => {
  ElMessage.success('库存数据导出成功');
  exportDialogVisible.value = false;
};

const handleExportError = () => {
  ElMessage.error('库存数据导出失败');
};
onMounted(async() => {
  await fetchStockData()
  await fetchStatistics()
})
const fetchStockData = async () => {
  loading.value = true
  try {
    const params: any = {
      stroe_id: String(storeId.value),
      page: String(currentPage.value),
      page_size: String(pageSize.value),
      token: token.value
    }
    if (searchKeyword.value) {
      params.select = searchKeyword.value
    }
    // 不向后端传递计算得出的库存状态，因为后端可能不支持这种筛选
    // 库存状态筛选将在本地完成

    const response = await axiosInstance.post('/buyer_commodity_repertory_list',
      new URLSearchParams(params as Record<string, string>),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'access-token': token.value
        }
      }
    )

    if (response.data.success) {
      console.log(response.data.data);

      let transformedData: StockItem[] = [];
      response.data.data.forEach((item: any) => {
        if (item.specifications && item.specifications.length > 0) {
          item.specifications.forEach((spec: any) => {
            transformedData.push({
              id: `${item.shopping_id}`,
              productId: item.shopping_id,
              name: item.name,
              specification: spec.specification_id.toString(),
              currentStock: spec.stock || 0,
              minStock: spec.minimum_balance || 0,
              maxStock: spec.maximum_inventory || 0,
              lastUpdated: spec.time || item.time
            });
          });
        } else {
          transformedData.push({
            id: item.shopping_id,
            productId: item.shopping_id,
            name: item.name,
            specification: '无规格',
            currentStock: 0,
            minStock: 0,
            maxStock: 0,
            lastUpdated: item.time
          });
        }
      });
      console.log(transformedData);

      // 如果有库存状态筛选条件，则进行本地过滤
      if (stockStatus.value) {
        transformedData = transformedData.filter(item =>
          filterByStockStatus(item, stockStatus.value)
        )
        // 更新总数为过滤后的数量
        total.value = transformedData.length
      } else {
        total.value = response.data.total
      }

      stockList.value = transformedData
    } else {
      ElMessage.error(response.data.msg || '获取库存数据失败')
    }
  } catch (error) {
    console.error('获取库存数据失败:', error)
    ElMessage.error('获取库存数据失败')
  } finally {
    loading.value = false
  }
}

const fetchStatistics = async () => {
  try {
    const params: any = {
      stroe_id: String(storeId.value),
      token: token.value
    }

    const response = await axiosInstance.post('/buyer_commodity_repertory_statistics',
      new URLSearchParams(params as Record<string, string>),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'access-token': token.value
        }
      }
    )

    if (response.data.success) {
      const data = response.data.data
      lowStockCount.value = data.low_stock_count || 0
      normalStockCount.value = data.normal_stock_count || 0
      totalStockCount.value = data.total_inventory || 0
      totalProducts.value = data.total_products || 0
    } else {
      ElMessage.error(response.data.msg || '获取统计数据失败')
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
    ElMessage.error('获取统计数据失败')
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchStockData()
}

// 辅助函数：根据库存状态筛选
const filterByStockStatus = (item: StockItem, status: string) => {
  const currentStatus = getStockStatusText(item.currentStock, item.minStock)
  return currentStatus === status
}

const handleSearchInput = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    handleSearch()
  }, 500)
}

const handleSelectionChange = (selection: StockItem[]) => {
  selectedItems.value = selection
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  fetchStockData()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchStockData()
}

const handleEditStock = (row: StockItem) => {
  stockForm.id = row.productId  // 使用原始商品ID而不是组合ID
  stockForm.name = row.name
  stockForm.currentStock = row.currentStock
  stockForm.minStock = row.minStock
  stockForm.maxStock = row.maxStock
  stockForm.specificationId = row.specification  // 保存规格ID
  stockForm.changeType = 'increase'
  stockForm.changeAmount = 0
  stockForm.remark = ''
  editDialogVisible.value = true
}

const handleStockRecord = async (row: StockItem) => {
  recordDialogVisible.value = true
  recordLoading.value = true

  try {
    const params: any = {
      product_id: String(row.productId),  // 使用原始商品ID而不是组合ID
      page: String(recordCurrentPage.value),
      page_size: String(recordPageSize.value),
      token: token.value
    }

    const framData = new FormData()
    framData.append('token', token.value)
    framData.append('stroe_id', String(storeId.value))
    framData.append('shopping_id', String(row.productId))
    framData.append('sku_id', String(row.specification))
    const response = await axiosInstance.post('/buyer_commodity_repertory_list_records',
      framData
    )

    if (response.data.current) {
      stockRecords.value = response.data.data.items || []
      recordTotal.value = response.data.data.total || 0
    } else {
      ElMessage.error(response.data.msg || '获取库存记录失败')
    }
  } catch (error) {
    console.error('获取库存记录失败:', error)
    ElMessage.error('获取库存记录失败')
  } finally {
    recordLoading.value = false
  }
}

const handleSubmitStock = async () => {
  if (!stockFormRef.value) return

  await stockFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        // 构建请求参数
        const formData = new FormData()
        formData.append('token', token.value)
        formData.append('stroe_id', String(storeId.value))
        formData.append('shopping_id', String(stockForm.id))
        formData.append('sku_id', String(stockForm.specificationId))

        if (stockForm.changeType != 'set') {
          formData.append('change_type', stockForm.changeType == 'increase' ? '1' : '0')
        }

        formData.append('change_num', String(stockForm.changeAmount))
        formData.append('maximum_inventory', String(stockForm.maxStock))
        formData.append('minimum_balance', String(stockForm.minStock))
        formData.append('info', stockForm.remark||'null')

        const res = await axiosInstance.patch('/buyer_commofity_inventory_change', formData)
        if (res.status == 200) {
          if (res.data.current) {
             await fetchStockData()
             await fetchStatistics()
            ElMessage.success('库存修改成功')

            editDialogVisible.value = false
            fetchStockData()
          } else {
            ElMessage.error(res.data.msg || '库存修改失败')
          }
        } else {
          ElMessage.error(res.data.msg || '库存修改失败')
        }


      } catch (error) {
        console.error('库存修改失败:', error)
        ElMessage.error('库存修改失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleBatchUpdate = () => {
  if (selectedItems.value.length === 0) {
    ElMessage.warning('请选择要批量修改的商品')
    return
  }
  ElMessageBox.confirm(
    `确定要对选中的 ${selectedItems.value.length} 个商品进行批量操作吗？`,
    '批量操作确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    ElMessage.info('批量修改功能开发中...')
  })
}



const handleRecordCurrentChange = (page: number) => {
  recordCurrentPage.value = page
}

const getStockClass = (currentStock: number, minStock: number) => {
  if (currentStock === 0) return 'stock-out'
  if (currentStock <= minStock) return 'stock-low'
  return 'stock-normal'
}

const getStockStatusType = (currentStock: number, minStock: number) => {
  if (currentStock === 0) return 'danger'
  if (currentStock <= minStock) return 'danger'
  if (currentStock <= minStock * 2) return 'warning'
  return 'success'
}

const getStockStatusText = (currentStock: number, minStock: number) => {
  if (currentStock === 0) return '缺货'
  if (currentStock <= minStock) return '库存不足'
  if (currentStock <= minStock * 2) return '库存较低'
  return '库存充足'
}

const getRecordTypeType = (type: string) => {
  switch (type) {
    case '增加': return 'success'
    case '减少': return 'danger'
    case '设置': return 'primary'
    default: return 'info'
  }
}

const getRecordTypeText = (type: string) => {
  switch (type) {
    case '1': return '增加'
    case '0': return '减少'
    case 'set': return '设置'
    default: return '其他'
  }
}

defineOptions({
  name: 'CommodityRepertory'
})
</script>

<style scoped>
.commodity-repertory-container {
  padding: 20px;
}

.statistics-row {
  margin-bottom: 20px;
}

.statistics-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.statistics-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
}

.statistics-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
  color: white;
}

.statistics-icon.warning {
  background: linear-gradient(135deg, #f56c6c, #e6a23c);
}

.statistics-icon.success {
  background: linear-gradient(135deg, #67c23a, #5cb85c);
}

.statistics-icon.info {
  background: linear-gradient(135deg, #409eff, #337ab7);
}

.statistics-icon.primary {
  background: linear-gradient(135deg, #409eff, #337ab7);
}

.statistics-content {
  flex: 1;
}

.statistics-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.statistics-label {
  font-size: 14px;
  color: #909399;
}

.search-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.list-card {
  border-radius: 8px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.stock-out {
  color: #f56c6c;
  font-weight: bold;
}

.stock-low {
  color: #e6a23c;
  font-weight: bold;
}

.stock-normal {
  color: #67c23a;
  font-weight: bold;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .commodity-repertory-container {
    padding: 10px;
  }

  .statistics-row {
    margin-bottom: 10px;
  }

  .statistics-card {
    margin-bottom: 10px;
  }

  .statistics-icon {
    width: 40px;
    height: 40px;
    font-size: 18px;
    margin-right: 10px;
  }

  .statistics-value {
    font-size: 18px;
  }

  .statistics-label {
    font-size: 12px;
  }
}
</style>
