<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <AppNavigation />
      </el-header>
      <el-main class="coupon-main">
        <div class="coupon-center">
          <h2 class="page-title">领券中心</h2>
          <el-empty v-if="!loading && coupons.length === 0" description="暂无可领取的优惠券" />

          <el-row :gutter="16" v-if="coupons.length > 0">
            <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in coupons" :key="item.id">
              <div class="coupon-card" :class="couponTypeClass(item.coupon_type)">
                <div class="coupon-left">
                  <div class="coupon-value">
                    <template v-if="item.coupon_type === 'full_reduction'">
                      <span class="symbol">¥</span>
                      <span class="amount">{{ item.discount_value }}</span>
                    </template>
                    <template v-else-if="item.coupon_type === 'discount'">
                      <span class="amount">{{ item.discount_value }}</span>
                      <span class="symbol">折</span>
                    </template>
                    <template v-else>
                      <span class="symbol">¥</span>
                      <span class="amount">{{ item.discount_value }}</span>
                    </template>
                  </div>
                  <div class="coupon-condition">
                    满{{ item.min_order_amount }}元可用
                  </div>
                </div>
                <div class="coupon-right">
                  <div class="coupon-name">{{ item.name }}</div>
                  <div class="coupon-scope">
                    <el-tag size="small" :type="item.issuer_type === 'platform' ? 'danger' : ''">
                      {{ item.issuer_type === 'platform' ? '平台券' : '店铺券' }}
                    </el-tag>
                    <el-tag size="small" type="info" style="margin-left:4px;">
                      {{ scopeLabel(item.scope) }}
                    </el-tag>
                  </div>
                  <div class="coupon-time">
                    {{ formatDate(item.start_time) }} - {{ formatDate(item.end_time) }}
                  </div>
                  <el-button
                    v-if="item.claim_status === 'claimed'"
                    size="small"
                    type="info"
                    disabled
                  >
                    已领取
                  </el-button>
                  <el-button
                    v-else-if="item.claim_status === 'sold_out'"
                    size="small"
                    type="info"
                    disabled
                  >
                    已领完
                  </el-button>
                  <el-button
                    v-else
                    size="small"
                    type="primary"
                    :loading="claimingId === item.id"
                    @click="handleClaim(item)"
                  >
                    立即领取
                  </el-button>
                </div>
              </div>
            </el-col>
          </el-row>

          <div class="pagination-wrap" v-if="total > pageSize">
            <el-pagination
              v-model:current-page="page"
              :page-size="pageSize"
              :total="total"
              layout="prev, pager, next"
              @current-change="loadCoupons"
            />
          </div>
        </div>
      </el-main>
      <el-footer class="footer-content">版权所有 © [xb商城]，保留所有权利。</el-footer>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import AppNavigation from '@/moon/navigation.vue'

const router = useRouter()
const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

const coupons = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const claimingId = ref<number | null>(null)

const getHeaders = () => {
  const token = localStorage.getItem('access_token')
  return token ? { 'access-token': token } : {}
}

const loadCoupons = async () => {
  loading.value = true
  try {
    const res = await Axios.get('/user_coupon/available', {
      params: { page: page.value, page_size: pageSize },
      headers: getHeaders(),
    })
    if (res.data?.success) {
      coupons.value = res.data.list
      total.value = res.data.total
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleClaim = async (item: any) => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    ElMessage.warning('请先登录')
    router.push('/register')
    return
  }

  claimingId.value = item.id
  try {
    const res = await Axios.post('/user_coupon/claim',
      { coupon_id: item.id },
      { headers: getHeaders() },
    )
    if (res.data?.success) {
      ElMessage.success('领取成功')
      await loadCoupons()
    } else {
      ElMessage.warning(res.data?.msg || '领取失败')
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.msg || '领取失败')
  } finally {
    claimingId.value = null
  }
}

const couponTypeClass = (type: string) => `coupon-${type}`

const scopeLabel = (scope: string) => {
  const map: Record<string, string> = {
    all_mall: '全商城可用',
    store: '指定店铺',
    product: '指定商品',
  }
  return map[scope] || scope
}

const formatDate = (d: string | null) => {
  if (!d) return ''
  return d.substring(0, 10)
}

onMounted(() => {
  loadCoupons()
})
</script>

<style scoped>
.coupon-main {
  min-height: calc(100vh - 120px);
}
.coupon-center {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}
.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
  text-align: center;
}
.coupon-card {
  display: flex;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s;
}
.coupon-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}
.coupon-left {
  width: 120px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 16px 12px;
  color: #fff;
  flex-shrink: 0;
}
.coupon-full_reduction .coupon-left { background: linear-gradient(135deg, #ff6b6b, #ee5a24); }
.coupon-discount .coupon-left { background: linear-gradient(135deg, #4834d4, #6c5ce7); }
.coupon-fixed_amount .coupon-left { background: linear-gradient(135deg, #f0932b, #ffbe76); }
.coupon-value {
  display: flex;
  align-items: baseline;
}
.coupon-value .symbol {
  font-size: 14px;
  margin-right: 2px;
}
.coupon-value .amount {
  font-size: 32px;
  font-weight: bold;
  line-height: 1;
}
.coupon-condition {
  font-size: 12px;
  margin-top: 6px;
  opacity: 0.9;
}
.coupon-right {
  flex: 1;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
}
.coupon-name {
  font-size: 15px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.coupon-time {
  font-size: 12px;
  color: #999;
}
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
.footer-content {
  text-align: center;
  color: darkgray;
}
</style>
