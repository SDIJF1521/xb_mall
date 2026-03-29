<template>
  <div class="my-coupons">
    <h3>我的优惠券</h3>

    <el-tabs v-model="activeTab" @tab-change="loadCoupons">
      <el-tab-pane label="未使用" name="unused" />
      <el-tab-pane label="已使用" name="used" />
      <el-tab-pane label="已过期" name="expired" />
    </el-tabs>

    <el-empty v-if="!loading && coupons.length === 0" description="暂无优惠券" :image-size="80" />

    <div class="coupon-list">
      <div v-for="item in coupons" :key="item.id"
           class="coupon-item" :class="{ 'coupon-disabled': activeTab !== 'unused' }">
        <div class="coupon-left" :class="couponBgClass(item.coupon_type)">
          <div class="coupon-value">
            <template v-if="item.coupon_type === 'full_reduction'">
              <span class="symbol">¥</span><span class="amount">{{ item.discount_value }}</span>
            </template>
            <template v-else-if="item.coupon_type === 'discount'">
              <span class="amount">{{ item.discount_value }}</span><span class="symbol">折</span>
            </template>
            <template v-else>
              <span class="symbol">¥</span><span class="amount">{{ item.discount_value }}</span>
            </template>
          </div>
          <div class="coupon-condition">满{{ item.min_order_amount }}元</div>
        </div>
        <div class="coupon-right">
          <div class="coupon-name">{{ item.name }}</div>
          <div class="coupon-info">
            <el-tag size="small" :type="item.issuer_type === 'platform' ? 'danger' : ''">
              {{ item.issuer_type === 'platform' ? '平台券' : '店铺券' }}
            </el-tag>
          </div>
          <div class="coupon-time">
            {{ formatDate(item.start_time) }} - {{ formatDate(item.end_time) }}
          </div>
          <div class="coupon-status" v-if="activeTab === 'used'">
            <span class="used-badge">已使用</span>
            <span v-if="item.order_no" class="order-link">订单: {{ item.order_no }}</span>
          </div>
          <div class="coupon-status" v-else-if="activeTab === 'expired'">
            <span class="expired-badge">已过期</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

const activeTab = ref('unused')
const coupons = ref<any[]>([])
const loading = ref(false)

const getHeaders = () => {
  const token = localStorage.getItem('access_token')
  return token ? { 'access-token': token } : {}
}

const loadCoupons = async () => {
  loading.value = true
  try {
    const res = await Axios.get('/user_coupon/mine', {
      params: { status: activeTab.value || undefined },
      headers: getHeaders(),
    })
    if (res.data?.success) {
      coupons.value = res.data.list || []
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const couponBgClass = (type: string) => `bg-${type}`
const formatDate = (d: string | null) => d ? d.substring(0, 10) : ''

onMounted(() => {
  loadCoupons()
})
</script>

<style scoped>
.my-coupons {
  width: 100%;
  max-width: 700px;
  padding: 20px;
}
.coupon-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.coupon-item {
  display: flex;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
}
.coupon-disabled {
  opacity: 0.55;
}
.coupon-left {
  width: 100px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 14px 10px;
  color: #fff;
  flex-shrink: 0;
}
.bg-full_reduction { background: linear-gradient(135deg, #ff6b6b, #ee5a24); }
.bg-discount { background: linear-gradient(135deg, #4834d4, #6c5ce7); }
.bg-fixed_amount { background: linear-gradient(135deg, #f0932b, #ffbe76); }
.coupon-value {
  display: flex;
  align-items: baseline;
}
.coupon-value .symbol { font-size: 13px; }
.coupon-value .amount { font-size: 28px; font-weight: bold; line-height: 1; }
.coupon-condition { font-size: 11px; margin-top: 4px; opacity: 0.9; }
.coupon-right {
  flex: 1;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  justify-content: center;
}
.coupon-name { font-size: 14px; font-weight: 500; }
.coupon-time { font-size: 12px; color: #999; }
.used-badge {
  color: #999;
  font-size: 12px;
  font-weight: 500;
}
.expired-badge {
  color: #c0c4cc;
  font-size: 12px;
}
.order-link {
  margin-left: 8px;
  font-size: 12px;
  color: #409eff;
}
</style>
