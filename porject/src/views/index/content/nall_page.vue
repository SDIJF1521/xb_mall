<template>
  <div class="product-showcase">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-grid">
        <div v-for="n in 6" :key="n" class="loading-card">
          <el-skeleton animated>
            <template #template>
              <el-skeleton-item variant="image" style="width: 100%; height: 280px" />
              <div style="padding: 24px">
                <el-skeleton-item variant="h3" style="width: 80%" />
                <div style="margin-top: 16px">
                  <el-skeleton-item variant="text" style="width: 100%" />
                  <el-skeleton-item variant="text" style="width: 60%; margin-top: 8px" />
                </div>
                <div style="margin-top: 20px">
                  <el-skeleton-item variant="text" style="width: 40%" />
                </div>
              </div>
            </template>
          </el-skeleton>
        </div>
      </div>
    </div>

    <!-- 商品网格 -->
    <div v-else-if="products.length > 0" class="products-grid">
      <div
        v-for="(product, index) in products"
        :key="product.id"
        class="product-card"
        @click="handleProductClick(product)"
        :style="{ animationDelay: `${index * 0.1}s` }"
      >
        <div class="product-image-container">
          <div class="image-wrapper">
            <el-image
              :src="product.image || '/placeholder-product.jpg'"
              :alt="product.name"
              class="product-image"
              fit="cover"
              lazy
            >
              <template #error>
                <div class="image-error">
                  <el-icon><Picture /></el-icon>
                </div>
              </template>
            </el-image>
          </div>

        </div>

        <div class="product-info">
          <div class="product-header">
            <h3 class="product-name">{{ product.name }}</h3>
            <el-tag size="small" type="info" class="product-category">{{ product.category }}</el-tag>
          </div>
          <p class="product-description">{{ product.description }}</p>

          <div class="product-price">
            <span class="current-price">¥{{ product.price }}</span>
            <span v-if="product.originalPrice" class="original-price">
              ¥{{ product.originalPrice }}
            </span>
          </div>

          <div class="product-stats">
            <div class="stat-item">
              <el-icon><ShoppingBag /></el-icon>
              <span>已售 {{ product.sales }}</span>
            </div>
            <div class="stat-item rating-item">
              <el-rate
                v-model="product.rating"
                disabled
                size="small"
              />
              <span class="rating-text">{{ product.rating }}</span>
            </div>
          </div>

          <div class="product-actions">
            <el-button
              type="primary"
              size="default"
              @click.stop="handleAddToCart(product)"
              :loading="cartLoading[product.id]"
              class="add-to-cart-btn"
            >
              <el-icon><ShoppingCart /></el-icon>
              加入购物车
            </el-button>
            <el-button
              size="default"
              @click.stop="handleAddToWishlist(product)"
              :type="product.isWishlisted ? 'danger' : 'default'"
              class="wishlist-btn"
              circle
            >
              <el-icon><Star /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-container">
      <el-empty
        description="暂无商品"
        :image-size="200"
      >
        <template #description>
          <p>暂无商品展示</p>
          <p class="empty-subtitle">敬请期待更多商品</p>
        </template>
      </el-empty>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, jumper, total"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { ShoppingCart, Star, Picture, ShoppingBag } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

// 定义商品接口
interface Product {
  id: number
  name: string
  description: string
  price: number
  originalPrice?: number
  image: string
  sales: number
  rating: number
  isWishlisted: boolean
  category: string
  stock: number
}

// 组件配置
defineOptions({
  name: 'NallPage'
})

// 路由
const router = useRouter()

// 响应式数据
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)
const cartLoading = reactive<Record<number, boolean>>({})

// 商品列表
const products = ref<Product[]>([])

// 假数据生成函数
const generateMockProducts = (page: number, size: number): Product[] => {
  const mockProducts: Product[] = []
  const startId = (page - 1) * size + 1

  for (let i = 0; i < size; i++) {
    const id = startId + i
    mockProducts.push({
      id,
      name: `商品名称 ${id}`,
      description: `这是商品 ${id} 的详细描述，展示商品的特点和优势。`,
      price: Math.floor(Math.random() * 900) + 100,
      originalPrice: Math.random() > 0.5 ? Math.floor(Math.random() * 1200) + 200 : undefined,
      image: `https://picsum.photos/300/300?random=${id}`,

      sales: Math.floor(Math.random() * 1000),
      rating: Math.round((Math.random() * 2 + 3) * 10) / 10,
      isWishlisted: Math.random() > 0.8,
      category: ['电子产品', '服装', '家居', '食品', '图书'][Math.floor(Math.random() * 5)],
      stock: Math.floor(Math.random() * 100)
    })
  }

  return mockProducts
}

// 获取商品列表
const fetchProducts = async (page: number = 1) => {
  try {
    loading.value = true

    // TODO: 替换为实际的API调用
    // const response = await axios.get('/api/products', {
    //   params: {
    //     page,
    //     pageSize: pageSize.value,
    //     category: selectedCategory.value,
    //     sort: sortBy.value
    //   }
    // })
    // products.value = response.data.products
    // total.value = response.data.total

    // 模拟API延迟
    await new Promise(resolve => setTimeout(resolve, 800))

    // 使用假数据
    products.value = generateMockProducts(page, pageSize.value)
    total.value = 100 // 模拟总商品数

  } catch (error) {
    console.error('获取商品列表失败:', error)
    ElMessage.error('获取商品列表失败')
  } finally {
    loading.value = false
  }
}

// 处理页码变化
const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchProducts(page)
  // 滚动到顶部
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 处理商品点击 - 跳转到商品详情页
const handleProductClick = (product: Product) => {
  console.log('点击商品:', product)

  // TODO: 配置商品跳转链接
  // 在这里配置你的商品跳转逻辑，例如：

  // 方式1: 内部路由跳转（需要在router中定义对应路由）
  // router.push({
  //   name: 'ProductDetail',
  //   params: { id: product.id }
  // })

  // 方式2: 外部链接跳转
  // window.open('https://your-external-link.com/product/' + product.id, '_blank')

  // 方式3: 新标签页打开内部路由
  // const route = router.resolve({
  //   name: 'ProductDetail',
  //   params: { id: product.id }
  // })
  // window.open(route.href, '_blank')

  // 方式4: 当前页面跳转外部链接
  // window.location.href = 'https://your-external-link.com/product/' + product.id

  // 默认：暂不跳转，等待配置
  console.log('商品跳转功能已准备就绪，请在 handleProductClick 函数中配置跳转链接')
}

// 处理加入购物车
const handleAddToCart = async (product: Product) => {
  try {
    cartLoading[product.id] = true

    // TODO: 替换为实际的API调用
    // await axios.post('/api/cart/add', {
    //   productId: product.id,
    //   quantity: 1
    // })

    // 模拟API延迟
    await new Promise(resolve => setTimeout(resolve, 500))

    ElMessage.success(`已将 ${product.name} 加入购物车`)
  } catch (error) {
    console.error('加入购物车失败:', error)
    ElMessage.error('加入购物车失败')
  } finally {
    cartLoading[product.id] = false
  }
}

// 处理收藏
const handleAddToWishlist = async (product: Product) => {
  try {
    // TODO: 替换为实际的API调用
    // if (product.isWishlisted) {
    //   await axios.delete(`/api/wishlist/${product.id}`)
    // } else {
    //   await axios.post('/api/wishlist/add', {
    //     productId: product.id
    //   })
    // }

    // 模拟API延迟
    await new Promise(resolve => setTimeout(resolve, 300))

    product.isWishlisted = !product.isWishlisted
    ElMessage.success(product.isWishlisted ? '已添加到收藏' : '已取消收藏')
  } catch (error) {
    console.error('收藏操作失败:', error)
    ElMessage.error('收藏操作失败')
  }
}

// 生命周期
onMounted(() => {
  fetchProducts(1)
})
</script>

<style scoped lang="scss">
.product-showcase {
  padding: 24px 20px;
  max-width: 1280px;
  margin: 0 auto;
  background: var(--color-background-soft);
  min-height: 100vh;
}

.loading-container {
  padding: 40px 20px;
}

.loading-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.loading-card {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0.6;
  }
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.product-card {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  opacity: 0;
  animation: fadeInUp 0.6s ease forwards;

  &:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    border-color: rgba(255, 255, 255, 0.4);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.product-image-container {
  position: relative;
  width: 100%;
  height: 280px;
  overflow: hidden;
  background: linear-gradient(45deg, #f0f2f5, #e6e9ef);
}

.image-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.product-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.6s cubic-bezier(0.25, 0.8, 0.25, 1);

  .product-card:hover & {
    transform: scale(1.08);
  }
}

.image-error {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  color: #999;
  font-size: 24px;
}



.product-info {
  padding: 24px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fb 100%);
}

.product-name {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  letter-spacing: -0.5px;
}

.product-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 12px;
}

.product-category {
  flex-shrink: 0;
  background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  font-weight: 500;
}

.product-description {
  font-size: 14px;
  color: #7f8c8d;
  margin: 0 0 20px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  box-orient: vertical;
  line-height: 1.6;
  height: 45px;
  font-weight: 400;
}

.product-price {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.current-price {
  font-size: 24px;
  font-weight: 700;
  color: #e74c3c;
  text-shadow: 0 2px 4px rgba(231, 76, 60, 0.2);
}

.original-price {
  font-size: 16px;
  color: #95a5a6;
  text-decoration: line-through;
  font-weight: 400;
}

.product-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  font-size: 13px;
  color: #7f8c8d;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;

  .el-icon {
    font-size: 14px;
    color: #95a5a6;
  }
}

.rating-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rating-text {
  font-weight: 600;
  color: #f39c12;
}

.product-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.add-to-cart-btn {
  flex: 1;
  background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-weight: 600;
  padding: 12px 20px;
  height: 44px;
  border-radius: 22px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
  }

  &:active {
    transform: translateY(0);
  }
}

.wishlist-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 2px solid #e74c3c;
  background: white;
  color: #e74c3c;
  transition: all 0.3s ease;

  &:hover {
    transform: scale(1.1);
    box-shadow: 0 4px 12px rgba(231, 76, 60, 0.3);
  }

  &.el-button--danger {
    background: linear-gradient(45deg, #ff6b6b 0%, #ee5a24 100%);
    border: none;
    color: white;

    &:hover {
      transform: scale(1.1);
      box-shadow: 0 4px 12px rgba(238, 90, 36, 0.4);
    }
  }
}

.empty-container {
  padding: 80px 0;
  text-align: center;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  margin: 20px;
}

.empty-subtitle {
  font-size: 16px;
  color: #7f8c8d;
  margin-top: 12px;
  font-weight: 400;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 40px;
}

// 响应式设计
@media (max-width: 768px) {
  .product-showcase {
    padding: 24px 16px;
  }

  .products-grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
  }

  .product-image-container {
    height: 220px;
  }

  .product-info {
    padding: 20px;
  }

  .product-name {
    font-size: 17px;
  }

  .product-description {
    font-size: 14px;
    height: 45px;
  }

  .current-price {
    font-size: 20px;
  }

  .add-to-cart-btn {
    height: 40px;
    font-size: 14px;
  }

  .wishlist-btn {
    width: 40px;
    height: 40px;
  }
}

@media (max-width: 480px) {
  .products-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .product-image-container {
    height: 240px;
  }

  .product-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .product-category {
    align-self: flex-start;
  }
}
</style>
