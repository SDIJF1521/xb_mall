<template>
  <div class="commodity-section">
    <!-- 搜索栏：骨架 ↔ 真实输入框 -->
    <el-skeleton :loading="storeLoading" animated>
      <template #template>
        <el-skeleton-item variant="rect" class="ske-search" />
      </template>
      <template #default>
        <div class="search-bar">
          <el-input
            :model-value="keyword"
            placeholder="搜索本店商品..."
            clearable
            size="large"
            class="search-input"
            @update:model-value="emit('update:keyword', $event)"
            @keydown.enter="emit('search')"
            @clear="emit('clear-search')"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
            <template #append>
              <el-button :icon="Search" @click="emit('search')">搜索</el-button>
            </template>
          </el-input>
        </div>
      </template>
    </el-skeleton>

    <!-- 商品网格：骨架 ↔ 真实内容 -->
    <el-skeleton :loading="storeLoading || loading" animated>
      <template #template>
        <div class="product-grid">
          <div v-for="n in 12" :key="n" class="product-card ske-card">
            <el-skeleton-item variant="image" class="ske-card-img" />
            <div class="ske-card-body">
              <el-skeleton-item variant="h3" class="ske-card-name" />
              <el-skeleton-item variant="text" class="ske-card-desc" />
              <el-skeleton-item variant="text" class="ske-card-price" />
            </div>
          </div>
        </div>
      </template>

      <template #default>
        <!-- 空状态 -->
        <el-empty
          v-if="list.length === 0"
          :description="keyword ? '未找到匹配商品' : '该店铺暂无商品'"
          :image-size="120"
        >
          <template #extra>
            <el-button v-if="keyword" type="primary" @click="emit('clear-search')">清除搜索</el-button>
          </template>
        </el-empty>

        <!-- 商品网格 -->
        <div v-else class="product-grid">
          <div
            v-for="(item, index) in list"
            :key="`${item.mall_id}-${item.shopping_id}`"
            class="product-card"
            :style="{ animationDelay: `${index * 0.05}s` }"
            @click="emit('go-detail', item)"
          >
            <div class="card-img-wrap">
              <el-image
                v-if="item.img"
                :src="item.img.startsWith('data:') ? item.img : 'data:image/jpeg;base64,' + item.img"
                fit="cover"
                class="card-img"
                lazy
              />
              <div v-else class="card-img card-img--placeholder">
                <el-icon :size="36" class="placeholder-icon"><Picture /></el-icon>
              </div>
            </div>
            <div class="card-body">
              <div class="card-name">{{ item.name }}</div>
              <div v-if="item.info" class="card-desc">{{ item.info }}</div>
              <div class="card-footer">
                <span class="card-price">¥ {{ item.price.toFixed(2) }}</span>
                <div class="card-tags">
                  <el-tag
                    v-for="t in item.type.slice(0, 2)"
                    :key="t"
                    size="small"
                    type="info"
                    effect="plain"
                  >{{ t }}</el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </el-skeleton>

    <!-- 分页 -->
    <div v-if="!storeLoading && !loading && total > 0" class="pagination-wrap">
      <el-pagination
        :current-page="page"
        :page-size="pageSize"
        :page-sizes="[12, 24, 48]"
        :total="total"
        layout="total, sizes, prev, pager, next"
        background
        @current-change="emit('update:page', $event)"
        @size-change="emit('update:pageSize', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Search, Picture } from '@element-plus/icons-vue'

export interface CommodityItem {
  mall_id: number
  shopping_id: number
  name: string
  info: string
  type: string[]
  price: number
  img: string
}

defineProps<{
  list: CommodityItem[]
  loading: boolean
  storeLoading: boolean
  total: number
  page: number
  pageSize: number
  keyword: string
}>()

const emit = defineEmits<{
  (e: 'update:page', val: number): void
  (e: 'update:pageSize', val: number): void
  (e: 'update:keyword', val: string): void
  (e: 'search'): void
  (e: 'clear-search'): void
  (e: 'go-detail', item: CommodityItem): void
}>()
</script>

<style scoped lang="scss">
.commodity-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.search-bar {
  .search-input { max-width: 480px; }
}

/* ── 商品网格 ── */
.product-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;

  @media (max-width: 1100px) { grid-template-columns: repeat(3, 1fr); }
  @media (max-width: 760px)  { grid-template-columns: repeat(2, 1fr); }
  @media (max-width: 480px)  { grid-template-columns: 1fr; }
}

.product-card {
  border-radius: 16px;
  overflow: hidden;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.25, 0.8, 0.25, 1);
  opacity: 0;
  animation: fadeInUp 0.5s ease forwards;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    border-color: var(--color-border-hover);
  }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}

.card-img-wrap {
  width: 100%;
  height: 200px;
  overflow: hidden;
  background: var(--color-background-mute);

  .card-img {
    width: 100%;
    height: 100%;
    transition: transform 0.35s ease;
  }

  .card-img--placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    .placeholder-icon { color: #999; }
  }

  .product-card:hover & .card-img { transform: scale(1.03); }
}

.card-body {
  padding: 14px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.card-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--vt-c-text-light-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  letter-spacing: -0.2px;
}

.card-desc {
  font-size: 12px;
  color: var(--vt-c-text-light-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 6px;
  flex-wrap: wrap;
  gap: 6px;
}

.card-price {
  font-size: 17px;
  font-weight: 700;
  color: #e74c3c;
  text-shadow: 0 1px 2px rgba(231, 76, 60, 0.15);
}

.card-tags { display: flex; gap: 4px; flex-wrap: wrap; }

/* ── 分页 ── */
.pagination-wrap {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}

/* ── 骨架尺寸 ── */
.ske-search  { width: 480px; height: 40px; border-radius: 8px; max-width: 100%; }
.ske-card    { cursor: default; pointer-events: none; }
.ske-card-img   { width: 100%; height: 200px; border-radius: 0; }
.ske-card-body  { padding: 14px 16px 16px; display: flex; flex-direction: column; gap: 10px; }
.ske-card-name  { width: 85%; height: 18px; }
.ske-card-desc  { width: 60%; height: 14px; }
.ske-card-price { width: 40%; height: 18px; }

/* ── 暗色模式 ── */
html.dark .product-card {
  background: var(--vt-c-black);
  border-color: var(--vt-c-divider-dark-1);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);

  &:hover { box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35); border-color: var(--vt-c-divider-dark-2); }
}

html.dark .card-img-wrap { background: var(--vt-c-black-mute); }
html.dark .card-name     { color: var(--vt-c-text-dark-1); }
html.dark .card-desc     { color: var(--vt-c-text-dark-2); }
html.dark .card-price    { color: #f56c6c; }
</style>
