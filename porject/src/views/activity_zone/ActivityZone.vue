<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <AppNavigation />
      </el-header>
      <el-main class="activity-main">
        <div class="activity-zone">
          <h2 class="page-title">活动专区</h2>

          <div class="filter-bar">
            <el-radio-group v-model="filterType" @change="handleFilterChange">
              <el-radio-button value="">全部</el-radio-button>
              <el-radio-button value="flash_sale">限时秒杀</el-radio-button>
              <el-radio-button value="full_reduction">满减活动</el-radio-button>
              <el-radio-button value="discount">折扣活动</el-radio-button>
              <el-radio-button value="group_buy">拼团活动</el-radio-button>
            </el-radio-group>
          </div>

          <el-empty v-if="!loading && activities.length === 0" description="暂无进行中的活动" />

          <div v-for="act in activities" :key="act.id" class="activity-card" @click="showDetail(act)">
            <div class="activity-header">
              <div class="activity-title-row">
                <el-tag :type="activityTagType(act.activity_type)" size="small">
                  {{ activityTypeLabel(act.activity_type) }}
                </el-tag>
                <span class="activity-name">{{ act.name }}</span>
                <el-tag size="small" :type="act.issuer_type === 'platform' ? 'danger' : ''">
                  {{ act.issuer_type === 'platform' ? '平台活动' : '店铺活动' }}
                </el-tag>
              </div>
              <div class="activity-time">
                {{ formatDate(act.start_time) }} - {{ formatDate(act.end_time) }}
              </div>
              <div class="activity-desc" v-if="act.description">{{ act.description }}</div>
              <div class="activity-rules" v-if="act.rules">
                <template v-if="act.activity_type === 'flash_sale'">
                  限时秒杀价
                </template>
                <template v-else-if="act.activity_type === 'full_reduction'">
                  满{{ act.rules.threshold }}元减{{ act.rules.reduction }}元
                </template>
                <template v-else-if="act.activity_type === 'discount'">
                  {{ act.rules.discount_rate }}折优惠
                </template>
                <template v-else-if="act.activity_type === 'group_buy'">
                  {{ act.rules.group_size }}人成团
                </template>
              </div>
            </div>
          </div>

          <div class="pagination-wrap" v-if="total > pageSize">
            <el-pagination
              v-model:current-page="page"
              :page-size="pageSize"
              :total="total"
              layout="prev, pager, next"
              @current-change="loadActivities"
            />
          </div>
        </div>

        <!-- 活动详情弹窗 -->
        <el-dialog v-model="detailVisible" :title="detailData?.name" width="700px" destroy-on-close>
          <div v-if="detailLoading" style="text-align:center;padding:40px;">
            <el-icon class="is-loading" :size="32"><Loading /></el-icon>
          </div>
          <div v-else-if="detailData">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="活动类型">
                {{ activityTypeLabel(detailData.activity_type) }}
              </el-descriptions-item>
              <el-descriptions-item label="发布方">
                {{ detailData.issuer_type === 'platform' ? '平台' : '商家' }}
              </el-descriptions-item>
              <el-descriptions-item label="开始时间">{{ detailData.start_time }}</el-descriptions-item>
              <el-descriptions-item label="结束时间">{{ detailData.end_time }}</el-descriptions-item>
              <el-descriptions-item label="活动说明" :span="2">
                {{ detailData.description || '无' }}
              </el-descriptions-item>
            </el-descriptions>

            <h4 style="margin:16px 0 8px;">活动商品</h4>
            <el-empty v-if="!detailData.products || detailData.products.length === 0"
                       description="暂无活动商品" :image-size="60" />
            <el-table v-else :data="detailData.products" stripe size="small">
              <el-table-column prop="shopping_id" label="商品ID" width="90" />
              <el-table-column prop="mall_id" label="店铺ID" width="90" />
              <el-table-column prop="activity_price" label="活动价(¥)" width="110">
                <template #default="{ row }">
                  <span style="color:#f56c6c;font-weight:bold;">
                    {{ row.activity_price ? `¥${row.activity_price}` : '-' }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="activity_stock" label="活动库存" width="100" />
              <el-table-column prop="sold_count" label="已售" width="80" />
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <el-button size="small" type="primary" link
                    @click="goProduct(row.mall_id, row.shopping_id)">
                    去看看
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <div v-if="detailData.coupons && detailData.coupons.length > 0">
              <h4 style="margin:16px 0 8px;">活动优惠券</h4>
              <el-tag v-for="c in detailData.coupons" :key="c.coupon_id"
                      style="margin-right:8px;margin-bottom:4px;">
                {{ c.name }} ({{ couponTypeLabel(c.coupon_type) }})
              </el-tag>
            </div>
          </div>
        </el-dialog>
      </el-main>
      <el-footer class="footer-content">版权所有 © [xb商城]，保留所有权利。</el-footer>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { Loading } from '@element-plus/icons-vue'
import AppNavigation from '@/moon/navigation.vue'

const router = useRouter()
const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })

const activities = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const filterType = ref('')

const detailVisible = ref(false)
const detailLoading = ref(false)
const detailData = ref<any>(null)

const loadActivities = async () => {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize }
    if (filterType.value) params.activity_type = filterType.value
    const res = await Axios.get('/user_activity/list', { params })
    if (res.data?.success) {
      activities.value = res.data.list
      total.value = res.data.total
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  page.value = 1
  loadActivities()
}

const showDetail = async (act: any) => {
  detailVisible.value = true
  detailLoading.value = true
  try {
    const res = await Axios.get('/user_activity/detail', { params: { activity_id: act.id } })
    if (res.data?.success) {
      detailData.value = res.data.data
    }
  } catch (e) {
    console.error(e)
  } finally {
    detailLoading.value = false
  }
}

const goProduct = (mallId: number, shoppingId: number) => {
  detailVisible.value = false
  router.push(`/commodity/${mallId}/${shoppingId}`)
}

const activityTypeLabel = (t: string) => {
  const map: Record<string, string> = {
    flash_sale: '限时秒杀', full_reduction: '满减活动',
    discount: '折扣活动', group_buy: '拼团活动',
  }
  return map[t] || t
}

const activityTagType = (t: string) => {
  const map: Record<string, string> = {
    flash_sale: 'danger', full_reduction: 'warning',
    discount: '', group_buy: 'success',
  }
  return map[t] || ''
}

const couponTypeLabel = (t: string) => {
  const map: Record<string, string> = {
    full_reduction: '满减券', discount: '折扣券', fixed_amount: '立减券',
  }
  return map[t] || t
}

const formatDate = (d: string | null) => {
  if (!d) return ''
  return d.substring(0, 16)
}

onMounted(() => {
  loadActivities()
})
</script>

<style scoped>
.activity-main {
  min-height: calc(100vh - 120px);
}
.activity-zone {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}
.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 20px;
  text-align: center;
}
.filter-bar {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}
.activity-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  cursor: pointer;
  transition: all 0.2s;
}
.activity-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.15);
}
.activity-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.activity-name {
  font-size: 16px;
  font-weight: 600;
  flex: 1;
}
.activity-time {
  font-size: 13px;
  color: #999;
  margin-bottom: 4px;
}
.activity-desc {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}
.activity-rules {
  margin-top: 8px;
  font-size: 14px;
  color: #f56c6c;
  font-weight: 500;
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
