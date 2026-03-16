<template>
  <div class="mall-goods">
    <div class="section-header">
      <span class="section-title">为你推荐</span>
      <span class="section-sub">根据你的偏好精选商品</span>
    </div>
    <div class="goods-grid">
      <div
        v-for="item in goods"
        :key="item.shopping_id"
        class="goods-card"
        @click="goToDetail(item)"
      >
        <div class="goods-img-wrapper">
          <img
            v-if="item.img"
            :src="`data:image/jpeg;base64,${item.img}`"
            class="goods-img"
            :alt="item.name"
          />
          <div v-else class="goods-img-placeholder">
            <el-icon :size="40" color="#c0c4cc"><Picture /></el-icon>
          </div>
        </div>
        <div class="goods-info">
          <div class="goods-name" :title="item.name">{{ item.name }}</div>
          <div class="goods-desc" :title="item.info">{{ item.info }}</div>
          <div class="goods-tags">
            <el-tag
              v-for="tag in item.type"
              :key="tag"
              size="small"
              class="goods-tag"
              effect="plain"
            >{{ tag }}</el-tag>
          </div>
          <div class="goods-price">
            <span class="price-symbol">¥</span>
            <span class="price-value">{{ item.price }}</span>
          </div>
          <div class="goods-actions">
            <el-button
              type="primary"
              size="small"
              class="cart-btn"
              :loading="cartLoading[item.shopping_id]"
              @click.stop="handleAddToCart(item)"
            >
              <el-icon><ShoppingCart /></el-icon>
              加入购物车
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { Picture, ShoppingCart } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import ElMessage from '@/utils/message'
import axios from 'axios'

defineOptions({ name: 'MallGoods' })

interface GoodsItem {
  mall_id: string
  shopping_id: string
  name: string
  info: string
  type: string[]
  price: number
  img: string
}

defineProps<{
  goods: GoodsItem[]
}>()

const router = useRouter()

const cartLoading = reactive<Record<string, boolean>>({})

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

const getCartHeaders = () => {
  const token = localStorage.getItem('access_token') || localStorage.getItem('buyer_access_token')
  return token ? { 'access-token': token } : {}
}

const goToDetail = (item: GoodsItem) => {
  router.push(`/commodity/${item.mall_id}/${item.shopping_id}`)
}

const handleAddToCart = async (item: GoodsItem) => {
  const token = localStorage.getItem('access_token') || localStorage.getItem('buyer_access_token')
  if (!token) {
    ElMessage.warning('请先登录')
    router.push('/register')
    return
  }
  try {
    cartLoading[item.shopping_id] = true
    const res = await Axios.post(
      '/shopping_cart_add',
      {
        mall_id: item.mall_id,
        shopping_id: item.shopping_id,
        spec_index: 0,
        quantity: 1,
      },
      { headers: getCartHeaders() }
    )
    if (res.data.success) {
      ElMessage.success(`已将 ${item.name} 加入购物车`)
    } else {
      ElMessage.warning(res.data.msg || '操作失败')
    }
  } catch (error: unknown) {
    console.error('加入购物车失败:', error)
    const status = (error as { response?: { status?: number } })?.response?.status
    if (status === 401 || status === 403) {
      ElMessage.warning('请先登录')
      router.push('/register')
    } else {
      ElMessage.error('加入购物车失败')
    }
  } finally {
    cartLoading[item.shopping_id] = false
  }
}
</script>

<style scoped>
.mall-goods {
  padding: 16px 0;
}

.section-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 20px;
  padding: 0 4px;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}

.section-sub {
  font-size: 13px;
  color: #909399;
}

.goods-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.goods-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.goods-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
}

.goods-img-wrapper {
  width: 100%;
  aspect-ratio: 1 / 1;
  overflow: hidden;
  background: #f5f7fa;
}

.goods-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.goods-card:hover .goods-img {
  transform: scale(1.05);
}

.goods-img-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

.goods-info {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.goods-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.goods-desc {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.goods-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  min-height: 22px;
}

.goods-tag {
  font-size: 11px;
}

.goods-price {
  margin-top: 4px;
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.price-symbol {
  font-size: 13px;
  color: #f56c6c;
  font-weight: 600;
}

.price-value {
  font-size: 18px;
  font-weight: 700;
  color: #f56c6c;
}

.goods-actions {
  margin-top: 8px;
}

.cart-btn {
  width: 100%;
  border-radius: 20px;
  font-weight: 600;
  background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s ease;
}

.cart-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}
</style>
