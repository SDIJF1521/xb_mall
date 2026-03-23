<template>
  <el-container>
    <el-container>
      <BuyerNavigation />
      <el-container>
        <el-header>
          <BuyerHead />
        </el-header>
        <el-main>
          <div class="cs-select-container">
            <h2 class="page-title">客服管理</h2>
            <p class="page-subtitle">选择要管理客服的店铺</p>
          <!-- 骨架屏 -->
          <div v-if="loading" class="skeleton-wrap">
            <el-skeleton v-for="i in 3" :key="i" animated class="store-skeleton">
              <template #template>
                <div class="skeleton-card">
                  <el-skeleton-item variant="image" style="width:80px;height:80px;border-radius:12px" />
                  <div class="skeleton-right">
                    <el-skeleton-item variant="h3" style="width:40%;height:20px" />
                    <el-skeleton-item variant="text" style="width:60%;height:14px;margin-top:8px" />
                    <el-skeleton-item variant="button" style="width:120px;height:36px;margin-top:16px;border-radius:18px" />
                  </div>
                </div>
              </template>
            </el-skeleton>
          </div>

          <!-- 空状态 -->
          <el-empty
            v-else-if="storeList.length === 0"
            description="暂无店铺，请先创建店铺"
          >
            <el-button type="primary" @click="router.push('/buyer_add_mall')">立即创建</el-button>
          </el-empty>

          <!-- 店铺卡片列表 -->
          <div v-else class="content-info">
            <el-card
              v-for="item in storeList"
              :key="item.id"
              class="store-card"
              shadow="hover"
            >
              <template #header>
                <div class="card-header">
                  <div class="card-header-left">
                    <el-badge :value="item.unread_count" :hidden="!item.unread_count" :max="99" class="store-unread-badge">
                      <span class="store-name">{{ item.mall_name }}</span>
                    </el-badge>
                  </div>
                  <el-tag :type="item.state === 1 && item.state_platform === 1 ? 'success' : 'danger'" size="small">
                    {{ item.state === 1 && item.state_platform === 1 ? '营业中' : '已关闭' }}
                  </el-tag>
                </div>
              </template>
              <el-row :gutter="10" style="width: 100%;">
                <el-col :span="12">
                  <el-image
                    :src="item.img ? `data:image/png;base64,${item.img}` : defaultImg"
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
                      <span>{{ item.info || '暂无店铺描述' }}</span>
                    </div>
                    <div class="info-item">
                      <el-icon><Location /></el-icon>
                      <span>{{ item.site || '暂无地址信息' }}</span>
                    </div>
                    <div class="info-item">
                      <el-icon><Phone /></el-icon>
                      <span>{{ item.phone || '暂无联系电话' }}</span>
                    </div>
                    <el-badge :value="item.unread_count" :hidden="!item.unread_count" :max="99" class="enter-btn-badge">
                      <el-button
                        type="primary"
                        size="default"
                        round
                        class="select-btn"
                        :disabled="!(item.state === 1 && item.state_platform === 1)"
                        @click="enterService(item.id || 0)"
                      >
                        <el-icon><Headset /></el-icon>
                        进入客服管理
                      </el-button>
                    </el-badge>
                  </div>
                </el-col>
              </el-row>
              <template #footer>
                <div class="card-footer">
                  <el-icon><Clock /></el-icon>
                  <span>创建时间：{{ item.time || '未知' }}</span>
                </div>
              </template>
            </el-card>
          </div>
          </div>
        </el-main>
      </el-container>
    </el-container>
    <el-footer class="footer-content">版权所有 ©[小白的个人商城]，保留所有权利。</el-footer>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Headset, Shop, Phone, Location, Document, Clock } from '@element-plus/icons-vue'
import BuyerTheme from '@/moon/buyer_theme'
import BuyerNavigation from '@/moon/buyer_navigation.vue'
import BuyerHead from '@/moon/buyer_head.vue'

interface StoreItem {
  id?: number
  img?: string
  info?: string
  mall_name?: string
  phone?: string
  site?: string
  time?: string
  state?: number
  state_platform?: number
  unread_count?: number
}

const router = useRouter()
const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

const loading = ref(false)
const storeList = ref<StoreItem[]>([])

const defaultImg = 'https://img2.baidu.com/it/u=3422222222,2822222222&fm=253&fmt=auto&app=138&f=JPEG?w=500&h=500'

const fetchStoreUnreads = async (): Promise<Record<number, number>> => {
  const token = localStorage.getItem('buyer_access_token') || ''
  if (!token) return {}
  try {
    const res = await Axios.get('/cs_seller_store_unreads', { headers: { 'access-token': token } })
    if (res.data?.current && Array.isArray(res.data.data)) {
      const map: Record<number, number> = {}
      for (const item of res.data.data) {
        map[item.mall_id] = item.unread_count || 0
      }
      return map
    }
  } catch { /* ignore */ }
  return {}
}

const fetchStores = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('buyer_access_token') || ''
    const form = new FormData()
    form.append('token', token)
    const [storeRes, unreadMap] = await Promise.all([
      Axios.post('/buyer_get_mall_info', form),
      fetchStoreUnreads(),
    ])
    if (storeRes.data.current) {
      storeList.value = (storeRes.data.data || []).map((s: StoreItem) => ({
        ...s,
        unread_count: unreadMap[s.id || 0] || 0,
      }))
    } else {
      ElMessage.error('获取店铺列表失败')
    }
  } catch {
    ElMessage.error('网络异常，请稍后重试')
  } finally {
    loading.value = false
  }
}

const enterService = (mallId: number) => {
  if (!mallId) return
  router.push({ name: 'BuyerCustomerService', params: { mall_id: mallId } })
}

onMounted(() => {
  new BuyerTheme().initTheme()
  fetchStores()
})
</script>

<style scoped>
.footer-content {
  text-align: center;
  color: darkgray;
}

.el-header {
  border-bottom: 1px solid #514d4d;
  padding-bottom: 10px;
  margin-bottom: 10px;
}

.cs-select-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  text-align: center;
  font-size: 32px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
}

.page-subtitle {
  text-align: center;
  font-size: 16px;
  color: #7f8c8d;
  margin-bottom: 40px;
}

/* 骨架 */
.skeleton-wrap {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.store-skeleton {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 20px;
}

.skeleton-card {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.skeleton-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 店铺网格 */
.content-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  grid-gap: 20px;
}

.store-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  border: 1px solid #e8e8e8;
  overflow: hidden;
}

.store-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.store-card :deep(.el-card__header) {
  color: white;
  padding: 16px 20px;
  border-bottom: none;
}

.store-card :deep(.el-card__body) {
  padding: 0;
}

.store-card :deep(.el-card__footer) {
  padding: 12px 20px;
  border-top: 1px solid #e8e8e8;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header-left {
  display: flex;
  align-items: center;
}

.store-unread-badge :deep(.el-badge__content) {
  background: #f56c6c;
}

.enter-btn-badge :deep(.el-badge__content) {
  background: #f56c6c;
  top: -4px;
  right: 4px;
}

.store-name {
  font-size: 18px;
  font-weight: 600;
  color: white;
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

@media (max-width: 768px) {
  .cs-select-container {
    padding: 15px;
  }

  .page-title {
    font-size: 28px;
  }

  .page-subtitle {
    font-size: 14px;
    margin-bottom: 30px;
  }

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
</style>
