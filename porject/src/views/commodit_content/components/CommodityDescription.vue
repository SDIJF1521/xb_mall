<template>
  <div class="desc-panel">
    <!-- Tab 头 -->
    <div class="tab-header">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
        <span v-if="tab.key === 'spec' && props.specList?.length" class="tab-count">
          {{ props.specList.length }}
        </span>
      </button>
      <div class="tab-line" :style="lineStyle" />
    </div>

    <!-- 内容区 -->
    <div class="tab-body">
      <!-- 商品简介 -->
      <transition name="slide-fade" mode="out-in">
        <div v-if="activeTab === 'intro'" key="intro" class="intro-content">
          <div v-if="props.info" class="info-text">{{ props.info }}</div>
          <div v-else class="empty-tip">
            <el-icon :size="40"><Document /></el-icon>
            <p>暂无商品简介</p>
          </div>
        </div>

        <!-- 规格参数 -->
        <div v-else-if="activeTab === 'spec'" key="spec" class="spec-content">
          <template v-if="props.specList?.length">

            <!-- 汇总栏 -->
            <div class="spec-summary">
              <div class="ss-item">
                <span class="ss-num">{{ props.specList.length }}</span>
                <span class="ss-lbl">种规格</span>
              </div>
              <div class="ss-divider" />
              <div class="ss-item">
                <span class="ss-num price-range">
                  <template v-if="priceMin === priceMax">¥{{ priceMin }}</template>
                  <template v-else>¥{{ priceMin }} ~ ¥{{ priceMax }}</template>
                </span>
                <span class="ss-lbl">价格区间</span>
              </div>
              <div class="ss-divider" />
              <div class="ss-item">
                <span class="ss-num">{{ totalStock }}</span>
                <span class="ss-lbl">总库存（件）</span>
              </div>
              <div class="ss-divider" />
              <div class="ss-item">
                <span class="ss-num" :class="availableCount === 0 ? 'danger' : 'ok'">
                  {{ availableCount }}
                </span>
                <span class="ss-lbl">可购规格</span>
              </div>
            </div>

            <!-- 视图切换 -->
            <div class="view-toggle">
              <button :class="{ active: viewMode === 'card' }" @click="viewMode = 'card'">
                <el-icon><Grid /></el-icon> 卡片视图
              </button>
              <button :class="{ active: viewMode === 'table' }" @click="viewMode = 'table'">
                <el-icon><List /></el-icon> 表格对比
              </button>
            </div>

            <!-- 卡片视图 -->
            <div v-if="viewMode === 'card'" class="spec-cards">
              <div
                v-for="(spec, idx) in props.specList"
                :key="idx"
                class="spec-card"
                :class="{ 'is-out': spec.stock === 0 }"
              >
                <!-- 序号 + 名称 -->
                <div class="sc-head">
                  <span class="sc-index">{{ idx + 1 }}</span>
                  <span class="sc-name">{{ spec.specs?.join(' · ') || '—' }}</span>
                  <el-tag
                    class="sc-status-tag"
                    :type="spec.stock === 0 ? 'danger' : spec.stock <= 10 ? 'warning' : 'success'"
                    size="small"
                    effect="dark"
                  >
                    {{ spec.stock === 0 ? '售罄' : spec.stock <= 10 ? '紧张' : '充足' }}
                  </el-tag>
                </div>

                <!-- 价格 -->
                <div class="sc-price-block">
                  <span class="sc-price-sym">¥</span>
                  <span class="sc-price-val">{{ spec.price }}</span>
                </div>

                <!-- 库存进度 -->
                <div class="sc-stock-block">
                  <div class="sc-stock-meta">
                    <span class="sc-stock-label">库存</span>
                    <span class="sc-stock-num">
                      {{ spec.stock > 0 ? `${spec.stock} 件` : '已售罄' }}
                    </span>
                  </div>
                  <el-progress
                    :percentage="stockPercent(spec.stock)"
                    :color="stockColor(spec.stock)"
                    :stroke-width="6"
                    :show-text="false"
                    class="sc-progress"
                  />
                  <div class="sc-stock-hint">
                    <span v-if="spec.stock === 0" class="hint-danger">该规格暂无库存</span>
                    <span v-else-if="spec.stock <= 5" class="hint-warn">仅剩 {{ spec.stock }} 件，抓紧下单！</span>
                    <span v-else-if="spec.stock <= 10" class="hint-warn">库存紧张，剩余 {{ spec.stock }} 件</span>
                    <span v-else class="hint-ok">库存充足，放心购买</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 表格对比视图 -->
            <div v-else class="spec-table-wrap">
              <table class="spec-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>规格名称</th>
                    <th>单价</th>
                    <th>库存</th>
                    <th>库存状态</th>
                    <th>可购</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(spec, idx) in props.specList"
                    :key="idx"
                    :class="{ 'row-out': spec.stock === 0 }"
                  >
                    <td class="td-idx">{{ idx + 1 }}</td>
                    <td class="td-name">{{ spec.specs?.join(' · ') || '—' }}</td>
                    <td class="td-price">¥{{ spec.price }}</td>
                    <td class="td-stock">{{ spec.stock }} 件</td>
                    <td class="td-status">
                      <el-tag
                        :type="spec.stock === 0 ? 'danger' : spec.stock <= 10 ? 'warning' : 'success'"
                        size="small"
                        effect="light"
                      >
                        {{ spec.stock === 0 ? '已售罄' : spec.stock <= 10 ? '库存紧张' : '库存充足' }}
                      </el-tag>
                    </td>
                    <td class="td-avail">
                      <el-icon v-if="spec.stock > 0" color="#67C23A"><CircleCheckFilled /></el-icon>
                      <el-icon v-else color="#F56C6C"><CircleCloseFilled /></el-icon>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

          </template>
          <div v-else class="empty-tip">
            <el-icon :size="40"><Box /></el-icon>
            <p>暂无规格信息</p>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Document, Box, Grid, List, CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'

interface Spec {
  specs: string[]
  price: number
  stock: number
  specification_id?: number
}

const props = defineProps<{
  info?: string
  specList?: Spec[]
}>()

const tabs = [
  { key: 'intro', label: '商品简介' },
  { key: 'spec',  label: '规格参数' },
]

const activeTab = ref('intro')
const viewMode  = ref<'card' | 'table'>('card')

const lineStyle = computed(() => {
  const idx = tabs.findIndex(t => t.key === activeTab.value)
  return { transform: `translateX(${idx * 100}%)` }
})

const priceMin = computed(() =>
  props.specList?.length ? Math.min(...props.specList.map(s => s.price)) : 0
)
const priceMax = computed(() =>
  props.specList?.length ? Math.max(...props.specList.map(s => s.price)) : 0
)
const totalStock = computed(() =>
  props.specList?.reduce((sum, s) => sum + (s.stock || 0), 0) ?? 0
)
const availableCount = computed(() =>
  props.specList?.filter(s => s.stock > 0).length ?? 0
)
const maxStock = computed(() =>
  props.specList?.length ? Math.max(...props.specList.map(s => s.stock)) : 1
)

const stockPercent = (stock: number) => {
  if (!maxStock.value) return 0
  return Math.round((stock / maxStock.value) * 100)
}
const stockColor = (stock: number) => {
  if (stock === 0) return '#F56C6C'
  if (stock <= 5)  return '#F56C6C'
  if (stock <= 10) return '#E6A23C'
  return '#67C23A'
}
</script>

<style scoped lang="scss">
.desc-panel {
  border-radius: 20px;
  background: var(--el-bg-color);
  border: 1px solid var(--color-border);
  overflow: hidden;
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
}

/* ── Tab 头 ── */
.tab-header {
  position: relative;
  display: flex;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-background-soft);
}

.tab-btn {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 16px 28px;
  border: none;
  background: transparent;
  font-size: 15px;
  font-weight: 500;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  transition: color 0.2s;
  flex: 1;
  justify-content: center;

  &.active {
    color: #667eea;
    font-weight: 700;
  }

  .tab-count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #667eea22;
    color: #667eea;
    font-size: 11px;
    font-weight: 700;
  }
}

.tab-line {
  position: absolute;
  bottom: 0;
  left: 0;
  width: calc(100% / 2);
  height: 3px;
  border-radius: 3px 3px 0 0;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── 内容体 ── */
.tab-body {
  padding: 28px;
  min-height: 160px;
}

/* 简介 */
.intro-content {
  .info-text {
    font-size: 15px;
    line-height: 2;
    color: var(--el-text-color-regular);
    white-space: pre-wrap;
    word-break: break-word;
  }
}

/* ── 规格区 ── */
.spec-content { display: flex; flex-direction: column; gap: 20px; }

/* 汇总栏 */
.spec-summary {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 16px 20px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(102,126,234,0.06) 0%, rgba(118,75,162,0.06) 100%);
  border: 1px solid rgba(102,126,234,0.15);
}

.ss-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;

  .ss-num {
    font-size: 22px;
    font-weight: 800;
    color: var(--el-text-color-primary);
    line-height: 1;

    &.price-range { font-size: 16px; color: #e74c3c; }
    &.danger { color: #F56C6C; }
    &.ok    { color: #67C23A; }
  }

  .ss-lbl {
    font-size: 12px;
    color: var(--el-text-color-placeholder);
  }
}

.ss-divider {
  width: 1px;
  height: 32px;
  background: rgba(102,126,234,0.2);
}

/* 视图切换 */
.view-toggle {
  display: flex;
  gap: 8px;
  align-self: flex-end;

  button {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 6px 14px;
    border-radius: 8px;
    border: 1.5px solid var(--el-border-color);
    background: var(--el-bg-color);
    color: var(--el-text-color-secondary);
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;

    &:hover { border-color: #667eea; color: #667eea; }
    &.active {
      border-color: #667eea;
      background: rgba(102,126,234,0.08);
      color: #667eea;
      font-weight: 600;
    }
  }
}

/* 卡片网格 */
.spec-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.spec-card {
  padding: 18px;
  border-radius: 14px;
  background: var(--el-bg-color);
  border: 1.5px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 14px;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;

  &:hover:not(.is-out) {
    border-color: #667eea55;
    box-shadow: 0 6px 20px rgba(102,126,234,0.12);
    transform: translateY(-2px);
  }

  &.is-out {
    opacity: 0.6;
    background: var(--color-background-mute);
  }

  /* 头部 */
  .sc-head {
    display: flex;
    align-items: center;
    gap: 8px;

    .sc-index {
      width: 22px;
      height: 22px;
      border-radius: 6px;
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: #fff;
      font-size: 11px;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .sc-name {
      flex: 1;
      font-size: 14px;
      font-weight: 700;
      color: var(--el-text-color-primary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .sc-status-tag { flex-shrink: 0; }
  }

  /* 价格 */
  .sc-price-block {
    display: flex;
    align-items: baseline;
    gap: 2px;
    padding: 10px 14px;
    border-radius: 10px;
    background: var(--el-color-danger-light-9);
    border: 1px solid var(--el-color-danger-light-7);

    .sc-price-sym {
      font-size: 14px;
      font-weight: 600;
      color: #e74c3c;
    }

    .sc-price-val {
      font-size: 28px;
      font-weight: 800;
      color: #e74c3c;
      line-height: 1;
      letter-spacing: -0.5px;
    }
  }

  /* 库存 */
  .sc-stock-block {
    display: flex;
    flex-direction: column;
    gap: 6px;

    .sc-stock-meta {
      display: flex;
      align-items: center;
      justify-content: space-between;

      .sc-stock-label {
        font-size: 12px;
        color: var(--el-text-color-placeholder);
      }

      .sc-stock-num {
        font-size: 13px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
    }

    .sc-progress { margin: 0; }

    .sc-stock-hint {
      font-size: 11px;
      line-height: 1.5;

      .hint-danger { color: #F56C6C; }
      .hint-warn   { color: #E6A23C; }
      .hint-ok     { color: #67C23A; }
    }
  }
}

/* 表格视图 */
.spec-table-wrap {
  overflow-x: auto;
  border-radius: 12px;
  border: 1px solid var(--color-border);
}

.spec-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;

  thead tr {
    background: var(--color-background-soft);
  }

  th {
    padding: 12px 16px;
    text-align: left;
    font-size: 12px;
    font-weight: 600;
    color: var(--el-text-color-secondary);
    border-bottom: 1px solid var(--color-border);
    white-space: nowrap;
  }

  tbody tr {
    border-bottom: 1px solid var(--color-border);
    transition: background 0.15s;

    &:last-child { border-bottom: none; }
    &:hover { background: var(--color-background-soft); }
    &.row-out { opacity: 0.5; background: var(--color-background-mute); }
  }

  td {
    padding: 14px 16px;
    color: var(--el-text-color-primary);
    vertical-align: middle;
  }

  .td-idx {
    width: 40px;
    text-align: center;
    color: var(--el-text-color-placeholder);
    font-weight: 700;
  }

  .td-name { font-weight: 600; }

  .td-price {
    font-weight: 700;
    color: #e74c3c;
    font-size: 15px;
  }

  .td-stock { color: var(--el-text-color-regular); }

  .td-avail { text-align: center; font-size: 18px; }
}

/* 空状态 */
.empty-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  gap: 12px;
  color: var(--el-text-color-placeholder);

  p { font-size: 14px; margin: 0; }
}

/* 切换动画 */
.slide-fade-enter-active, .slide-fade-leave-active {
  transition: all 0.2s ease;
}
.slide-fade-enter-from { opacity: 0; transform: translateY(8px); }
.slide-fade-leave-to   { opacity: 0; transform: translateY(-8px); }
</style>
