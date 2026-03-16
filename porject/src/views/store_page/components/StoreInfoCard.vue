<template>
  <!-- 骨架 ↔ 真实内容原位切换 -->
  <el-skeleton :loading="loading" animated>
    <template #template>
      <div class="store-card">
        <el-skeleton-item variant="image" class="ske-avatar" />
        <div class="ske-meta">
          <el-skeleton-item variant="h3" class="ske-name" />
          <el-skeleton-item variant="text" class="ske-desc-1" />
          <el-skeleton-item variant="text" class="ske-desc-2" />
        </div>
        <div class="ske-actions">
          <el-skeleton-item variant="button" class="ske-btn" />
          <el-skeleton-item variant="button" class="ske-btn" />
        </div>
      </div>
    </template>

    <template #default>
      <div v-if="store" class="store-card">
        <!-- 店铺头像 -->
        <div class="store-avatar">
          <el-image
            v-if="store.img"
            :src="store.img.startsWith('data:') ? store.img : 'data:image/jpeg;base64,' + store.img"
            fit="cover"
            class="avatar-img"
          />
          <div v-else class="avatar-placeholder">
            <el-icon :size="36"><Shop /></el-icon>
          </div>
        </div>

        <!-- 店铺基本信息 -->
        <div class="store-meta">
          <h1 class="store-name">{{ store.mall_name }}</h1>
          <p v-if="store.info" class="store-desc">{{ store.info }}</p>
          <div class="store-tags">
            <span v-if="store.site" class="store-tag">
              <el-icon><Location /></el-icon>{{ store.site }}
            </span>
            <span v-if="store.phone" class="store-tag">
              <el-icon><Phone /></el-icon>{{ store.phone }}
            </span>
            <span v-if="store.create_time" class="store-tag">
              <el-icon><Calendar /></el-icon>{{ store.create_time.slice(0, 10) }} 开店
            </span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="store-actions">
          <!-- 收藏按钮（预留，逻辑待实现） -->
          <button
            class="btn-action"
            :class="{ 'btn-action--active': isFavorited }"
            @click="emit('favorite')"
          >
            <el-icon><component :is="isFavorited ? StarFilled : Star" /></el-icon>
            {{ isFavorited ? '已收藏' : '收藏店铺' }}
          </button>

          <!-- 客服按钮（预留，逻辑待实现） -->
          <button class="btn-action btn-action--primary" @click="emit('service')">
            <el-icon><Service /></el-icon>
            联系客服
          </button>
        </div>
      </div>
    </template>
  </el-skeleton>
</template>

<script setup lang="ts">
import { Shop, Location, Phone, Calendar, Star, StarFilled, Service } from '@element-plus/icons-vue'

export interface StoreInfo {
  mall_id: number
  mall_name: string
  phone: string
  site: string
  info: string
  img: string
  create_time: string
}

defineProps<{
  store: StoreInfo | null
  loading: boolean
  isFavorited: boolean
}>()

const emit = defineEmits<{
  (e: 'favorite'): void
  (e: 'service'): void
}>()
</script>

<style scoped lang="scss">
/* ── 店铺信息卡 ── */
.store-card {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 24px 28px;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  flex-wrap: wrap;
}

.store-avatar {
  flex-shrink: 0;
  width: 80px;
  height: 80px;
  border-radius: 12px;
  overflow: hidden;
  background: var(--color-background-mute);
  border: 1px solid var(--color-border);

  .avatar-img { width: 100%; height: 100%; }

  .avatar-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--vt-c-text-light-2);
  }
}

.store-meta {
  flex: 1;
  min-width: 0;
}

.store-name {
  font-size: 20px;
  font-weight: 600;
  color: var(--vt-c-text-light-1);
  margin: 0 0 6px;
  letter-spacing: -0.3px;
}

.store-desc {
  font-size: 14px;
  color: var(--vt-c-text-light-2);
  margin: 0 0 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.store-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.store-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--vt-c-text-light-2);

  .el-icon { font-size: 14px; }
}

.store-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.btn-action {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 40px;
  padding: 0 18px;
  border-radius: 12px;
  border: 1.5px solid var(--color-border-hover);
  background: var(--color-background);
  color: var(--vt-c-text-light-1);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;

  &:hover {
    border-color: #667eea;
    color: #667eea;
    background: rgba(102, 126, 234, 0.05);
    transform: translateY(-1px);
  }

  &--active {
    border-color: #e74c3c;
    color: #e74c3c;
    background: rgba(231, 76, 60, 0.05);
  }

  &--primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-color: transparent;
    color: #fff;

    &:hover {
      color: #fff;
      background: linear-gradient(135deg, #5a6fd6 0%, #6a3f96 100%);
      box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
    }
  }
}

/* ── 骨架尺寸 ── */
.ske-avatar  { flex-shrink: 0; width: 80px; height: 80px; border-radius: 12px; }
.ske-meta    { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 10px; }
.ske-name    { width: 160px; height: 22px; }
.ske-desc-1  { width: 100%; height: 14px; }
.ske-desc-2  { width: 55%; height: 14px; }
.ske-actions { display: flex; gap: 10px; flex-shrink: 0; }
.ske-btn     { width: 104px; height: 40px; border-radius: 12px; }

/* ── 暗色模式 ── */
html.dark .store-card {
  background: var(--vt-c-black-soft);
  border-color: var(--vt-c-divider-dark-1);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
}

html.dark .store-avatar {
  background: var(--vt-c-black-mute);
  border-color: var(--vt-c-divider-dark-1);
  .avatar-placeholder { color: var(--vt-c-text-dark-2); }
}

html.dark .store-name  { color: var(--vt-c-text-dark-1); }
html.dark .store-desc,
html.dark .store-tag   { color: var(--vt-c-text-dark-2); }

html.dark .btn-action {
  border-color: var(--vt-c-divider-dark-1);
  background: var(--vt-c-black-soft);
  color: var(--vt-c-text-dark-1);

  &:hover { border-color: #667eea; color: #667eea; background: rgba(102, 126, 234, 0.1); }
  &--active { border-color: #f56c6c; color: #f56c6c; background: rgba(245, 108, 108, 0.1); }
  &--primary { border-color: transparent; color: #fff;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
}
</style>
