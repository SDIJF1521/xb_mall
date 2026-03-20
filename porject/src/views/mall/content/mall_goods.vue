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
            <el-button
              size="small"
              :type="favState[item.shopping_id]?.wishlisted ? 'danger' : 'default'"
              :loading="wishlistLoading[item.shopping_id]"
              class="fav-btn"
              circle
              @click.stop="handleFavorite(item)"
            >
              <el-icon><Star /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import { Picture, ShoppingCart, Star } from '@element-plus/icons-vue'
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

const props = defineProps<{
  goods: GoodsItem[]
}>()

const router = useRouter()

const cartLoading = reactive<Record<string, boolean>>({})
const wishlistLoading = reactive<Record<string, boolean>>({})
const favState = reactive<Record<string, { wishlisted: boolean; favId: number | null }>>({})

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

const getCartHeaders = () => {
  const token = localStorage.getItem('access_token') || localStorage.getItem('buyer_access_token')
  return token ? { 'access-token': token } : {}
}

const batchCheckFavorites = async (items: GoodsItem[]) => {
  const token = localStorage.getItem('access_token')
  if (!token || items.length === 0) return
  const headers = { 'access-token': token }
  const checks = items.map((item) =>
    Axios.get('/favorite_check', {
      params: { type: 'commodity', mall_id: item.mall_id, shopping_id: item.shopping_id },
      headers,
    }).catch(() => null)
  )
  const results = await Promise.all(checks)
  results.forEach((res, idx) => {
    const key = items[idx].shopping_id
    if (res?.data?.success) {
      favState[key] = { wishlisted: res.data.is_favorited, favId: res.data.favorite_id ?? null }
    } else if (!favState[key]) {
      favState[key] = { wishlisted: false, favId: null }
    }
  })
}

watch(
  () => props.goods,
  (newGoods) => { if (newGoods.length) batchCheckFavorites(newGoods) },
  { immediate: true }
)

const handleFavorite = async (item: GoodsItem) => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    ElMessage.warning('请先登录')
    router.push('/register')
    return
  }
  const key = item.shopping_id
  const headers = { 'access-token': token }
  wishlistLoading[key] = true
  try {
    const state = favState[key]
    if (state?.wishlisted && state.favId) {
      const res = await Axios.delete('/favorite_remove', { params: { id: state.favId }, headers })
      if (res.data.success) {
        favState[key] = { wishlisted: false, favId: null }
        ElMessage.success('已取消收藏')
      } else {
        ElMessage.warning(res.data.msg || '操作失败')
      }
    } else {
      const res = await Axios.post(
        '/favorite_add',
        { type: 'commodity', mall_id: item.mall_id, shopping_id: item.shopping_id },
        { headers },
      )
      if (res.data.success) {
        const checkRes = await Axios.get('/favorite_check', {
          params: { type: 'commodity', mall_id: item.mall_id, shopping_id: item.shopping_id },
          headers,
        })
        favState[key] = {
          wishlisted: true,
          favId: checkRes.data?.favorite_id ?? null,
        }
        ElMessage.success('已添加到收藏')
      } else {
        ElMessage.warning(res.data.msg || '操作失败')
      }
    }
  } catch {
    ElMessage.error('收藏操作失败')
  } finally {
    wishlistLoading[key] = false
  }
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
  display: flex;
  align-items: center;
  gap: 8px;
}

.cart-btn {
  flex: 1;
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

.fav-btn {
  flex-shrink: 0;
  border: 1.5px solid #e74c3c;
  color: #e74c3c;
  transition: all 0.3s ease;
}

.fav-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(231, 76, 60, 0.3);
}

.fav-btn.el-button--danger {
  background: linear-gradient(45deg, #ff6b6b 0%, #ee5a24 100%);
  border: none;
  color: #fff;
}
</style>
