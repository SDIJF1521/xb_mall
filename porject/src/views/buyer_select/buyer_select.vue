<template>
  <el-container>
    <el-header>
      <div class="management-navigation">
        <h2 class="title">小白的商城-店铺选择</h2>
      </div>
    </el-header>
    <el-main>
      <div v-if="storeList.length > 0" class="content-info">
        <el-card v-for="store in filteredStores" :key="store.id" style="width: 100%;" class="store-card">
          <template #header>
            <div class="card-header">
              <span class="store-name">{{ store.mall_name }}</span>
              <el-tag :type="store.state === 1 ? 'success' : 'danger'" size="small">
                {{ store.state === 1 ? '营业中' : '已关闭' }}
              </el-tag>
            </div>
          </template>
          <el-row :gutter="10" style="width: 100%;">
            <el-col :span="12">
              <el-image
                :src="store.img ? 'data:image/png;base64,' + store.img : defaultStoreImg"
                style="width: 100%; height: 200px; object-fit: cover;"
                fit="cover"
              >
                <template #error>
                  <div class="image-slot">
                    <el-icon><Shop /></el-icon>
                    <span>暂无图片</span>
                  </div>
                </template>
              </el-image>
            </el-col>
            <el-col :span="12">
              <div class="store-info">
                <div class="info-item">
                  <el-icon><Document /></el-icon>
                  <span>{{ store.info || '暂无店铺描述' }}</span>
                </div>
                <div class="info-item">
                  <el-icon><Location /></el-icon>
                  <span>{{ store.site || '暂无地址信息' }}</span>
                </div>
                <div class="info-item">
                  <el-icon><Phone /></el-icon>
                  <span>{{ store.phone || '暂无联系电话' }}</span>
                </div>
                <el-button
                  type="primary"
                  size="default"
                  @click="selectStore(store.id || 0)"
                  round
                  class="select-btn"
                >
                  <el-icon><Check /></el-icon>
                  选择店铺
                </el-button>
              </div>
            </el-col>
          </el-row>
          <template #footer>
            <div class="card-footer">
              <el-icon><Clock /></el-icon>
              <span>创建时间：{{ store.time || '未知' }}</span>
            </div>
          </template>
        </el-card>
      </div>
      <el-empty v-else description="暂无店铺信息" />
    </el-main>
    <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useBuyerManagementSelectStore } from '@/moon/buyer_management_select'
import { Search, Refresh, Document, Location, Phone, Clock, Shop, Check } from '@element-plus/icons-vue'
import BuyerTheme from '@/moon/buyer_theme'
import router from '@/router'

defineOptions({
  name: 'BuyerSelect',
})

const Axios = axios.create({
  baseURL: "http://127.0.0.1:8000/api"
})

interface Store {
  id?: number
  mall_name: string
  state: number
  img: string
  info: string
  site: string
  phone: string
  time: string
}

const searchQuery = ref('')
const storeList = ref<Store[]>([])
const token = localStorage.getItem('buyer_access_token')
const defaultStoreImg = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'

const filteredStores = computed(() => {
  if (!searchQuery.value) {
    return storeList.value
  }
  return storeList.value.filter(store =>
    store.mall_name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    store.info.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const handleRefresh = async () => {
  ElMessage.success('店铺列表已刷新')
  await loadStoreData()
}

const selectStore = (id: number) => {
  const store = useBuyerManagementSelectStore()
  let toUel = store.getToUel()

  // 如果toUel为空，提供一个默认值
  if (!toUel) {
    toUel = '/buyer_store_manage'
  }

  console.log(toUel);
  console.log(toUel + `/${id}`);
  router.push(toUel + `/${id}`)
}

const loadStoreData = async () => {
  const form = new FormData()
  form.append('token', token || '')
  const res = await Axios.post("/buyer_get_mall_info", form)
  if (res.status == 200) {
    if (res.data.current) {
      storeList.value = res.data.data
      console.log(storeList.value)
    }
  }
}

onMounted(() => {
  new BuyerTheme().toggleTheme(true)
  // 初始化store
  useBuyerManagementSelectStore().init()
  loadStoreData()
})
</script>

<style scoped>
.footer-content {
  text-align: center;
  color: darkgray;
}

.title {
  background: linear-gradient(to right, #44baed, #9c6edd);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.management-navigation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  width: 100%;
}


.content-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  grid-gap: 20px;
  padding: 0 20px;
  max-width: 1200px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .content-info {
    grid-template-columns: 1fr;
    padding: 0 10px;
  }

  .el-row {
    flex-direction: column;
  }

  .el-col {
    width: 100%;
  }

  .store-info {
    height: auto;
    padding: 15px 20px;
    gap: 15px;
  }

  .store-card :deep(.el-card__header) {
    padding: 12px 15px;
  }

  .store-name {
    font-size: 16px;
  }
}

.store-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 200px;
  padding: 0 20px;
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.info-item .el-icon {
  color: #909399;
  margin-top: 2px;
  flex-shrink: 0;
}

.store-name {
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.select-btn {
  margin-top: auto;
  padding: 8px 16px;
  font-weight: 500;
}

.image-slot {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 200px;
  background-color: #f5f7fa;
  color: #909399;
  font-size: 14px;
}

.image-slot .el-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #909399;
  font-size: 13px;
}

.el-header {
  border-bottom: 1px solid #e0e0e0;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
