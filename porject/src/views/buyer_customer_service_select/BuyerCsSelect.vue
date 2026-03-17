<template>
  <el-container class="cs-select-root">
    <el-container>
      <!-- 左侧导航 -->
      <BuyerNavigation />

      <el-container class="cs-select-inner">
        <!-- 顶部头部 -->
        <el-header class="cs-select-head">
          <BuyerHead />
        </el-header>

        <!-- 页面标题栏 -->
        <div class="cs-page-title">
          <div class="title-left">
            <el-icon class="title-icon"><Headset /></el-icon>
            <span>客服管理</span>
          </div>
          <p class="title-sub">选择要管理客服的店铺</p>
        </div>

        <el-main class="cs-select-main">
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
          <div v-else class="store-grid">
            <div
              v-for="item in storeList"
              :key="item.id"
              class="store-card"
              :class="{ 'store-card--closed': !(item.state === 1 && item.state_platform === 1) }"
            >
              <!-- 店铺封面 -->
              <div class="card-cover">
                <el-image
                  :src="item.img ? `data:image/png;base64,${item.img}` : defaultImg"
                  fit="cover"
                  class="cover-img"
                >
                  <template #error>
                    <div class="cover-fallback">
                      <el-icon :size="32"><Shop /></el-icon>
                    </div>
                  </template>
                </el-image>
                <el-tag
                  class="state-tag"
                  :type="item.state === 1 && item.state_platform === 1 ? 'success' : 'danger'"
                  size="small"
                  effect="dark"
                >
                  {{ item.state === 1 && item.state_platform === 1 ? '营业中' : '已关闭' }}
                </el-tag>
              </div>

              <!-- 店铺信息 -->
              <div class="card-body">
                <h3 class="store-name">{{ item.mall_name }}</h3>
                <div v-if="item.info" class="store-desc">{{ item.info }}</div>
                <div class="store-meta">
                  <span v-if="item.phone" class="meta-item">
                    <el-icon><Phone /></el-icon>{{ item.phone }}
                  </span>
                  <span v-if="item.site" class="meta-item">
                    <el-icon><Location /></el-icon>{{ item.site }}
                  </span>
                </div>
              </div>

              <!-- 操作区 -->
              <div class="card-footer">
                <el-button
                  type="primary"
                  round
                  class="enter-btn"
                  :icon="Headset"
                  @click="enterService(item.id || 0)"
                >
                  进入客服管理
                </el-button>
              </div>
            </div>
          </div>
        </el-main>

        <el-footer class="cs-select-footer">版权所有 ©[小白的商城]，保留所有权利。</el-footer>
      </el-container>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Headset, Shop, Phone, Location } from '@element-plus/icons-vue'
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
}

const router = useRouter()
const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

const loading = ref(false)
const storeList = ref<StoreItem[]>([])

const defaultImg = 'https://img2.baidu.com/it/u=3422222222,2822222222&fm=253&fmt=auto&app=138&f=JPEG?w=500&h=500'

const fetchStores = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('buyer_access_token') || ''
    const form = new FormData()
    form.append('token', token)
    const res = await Axios.post('/buyer_get_mall_info', form)
    if (res.data.current) {
      storeList.value = res.data.data || []
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
  new BuyerTheme().toggleTheme(true)
  fetchStores()
})
</script>

<style scoped lang="scss">
.cs-select-root {
  min-height: 100vh;
}

.cs-select-inner {
  flex-direction: column;
  min-height: 100vh;
  background: var(--el-bg-color-page);
}

/* ── 顶部 head ── */
.cs-select-head {
  padding: 0;
  height: auto;
  border-bottom: 1px solid var(--el-border-color);
}

/* ── 页面标题栏 ── */
.cs-page-title {
  padding: 24px 32px 16px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.title-icon {
  font-size: 24px;
  color: #667eea;
}

.title-sub {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  padding-left: 34px;
}

/* ── Main ── */
.cs-select-main {
  padding: 24px 32px;
  flex: 1;
}

/* ── Footer ── */
.cs-select-footer {
  text-align: center;
  font-size: 13px;
  color: var(--el-text-color-placeholder);
  line-height: 60px;
}

/* 骨架 */
.skeleton-wrap {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.store-skeleton {
  background: var(--el-bg-color);
  border-radius: 16px;
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
.store-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.store-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 16px;
  overflow: hidden;
  transition: box-shadow 0.25s, transform 0.25s;
  display: flex;
  flex-direction: column;

  &:hover {
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    transform: translateY(-4px);
  }

  &--closed {
    opacity: 0.7;
  }
}

/* 封面 */
.card-cover {
  position: relative;
  height: 160px;
  overflow: hidden;
  flex-shrink: 0;
}

.cover-img {
  width: 100%;
  height: 100%;
}

.cover-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-placeholder);
}

.state-tag {
  position: absolute;
  top: 10px;
  right: 10px;
}

/* 卡片信息 */
.card-body {
  padding: 16px 18px 12px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.store-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.store-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.store-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 4px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  .el-icon { font-size: 13px; flex-shrink: 0; }
}

/* 底部按钮 */
.card-footer {
  padding: 12px 18px 18px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.enter-btn {
  width: 100%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  font-weight: 600;

  &:hover {
    opacity: 0.9;
  }
}
</style>
