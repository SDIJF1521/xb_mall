<template>
  <div class="gallery-root">
    <!-- 主图区 -->
    <div class="main-stage" @mousemove="onMouseMove" @mouseleave="onMouseLeave">
      <transition name="fade" mode="out-in">
        <el-image
          :key="activeIndex"
          :src="currentImage"
          fit="contain"
          class="main-img"
          :preview-src-list="props.imgList"
          :initial-index="activeIndex"
          preview-teleported
        >
          <template #error>
            <div class="img-placeholder">
              <el-icon :size="56"><Picture /></el-icon>
              <span>暂无图片</span>
            </div>
          </template>
          <template #placeholder>
            <div class="img-placeholder">
              <el-icon :size="36" class="is-loading"><Loading /></el-icon>
            </div>
          </template>
        </el-image>
      </transition>

      <!-- 放大镜提示 -->
      <div class="zoom-tip">
        <el-icon><ZoomIn /></el-icon>
        点击查看大图
      </div>

      <!-- 左右箭头 -->
      <template v-if="props.imgList.length > 1">
        <button class="nav-btn nav-prev" @click.stop="prev">
          <el-icon><ArrowLeft /></el-icon>
        </button>
        <button class="nav-btn nav-next" @click.stop="next">
          <el-icon><ArrowRight /></el-icon>
        </button>
        <!-- 圆点指示 -->
        <div class="dots">
          <span
            v-for="(_, i) in props.imgList"
            :key="i"
            class="dot"
            :class="{ active: i === activeIndex }"
            @click.stop="activeIndex = i"
          />
        </div>
      </template>
    </div>

    <!-- 缩略图条 -->
    <div v-if="props.imgList.length > 1" class="thumb-strip">
      <div
        v-for="(img, i) in props.imgList"
        :key="i"
        class="thumb-item"
        :class="{ active: i === activeIndex }"
        @click="activeIndex = i"
      >
        <el-image :src="img" fit="cover" class="thumb-img">
          <template #error>
            <div class="thumb-err"><el-icon><Picture /></el-icon></div>
          </template>
        </el-image>
        <div class="thumb-overlay" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Picture, Loading, ArrowLeft, ArrowRight, ZoomIn } from '@element-plus/icons-vue'

const props = defineProps<{ imgList: string[] }>()

const activeIndex = ref(0)
const currentImage = computed(() => props.imgList[activeIndex.value] ?? '')

const prev = () => { activeIndex.value = (activeIndex.value - 1 + props.imgList.length) % props.imgList.length }
const next = () => { activeIndex.value = (activeIndex.value + 1) % props.imgList.length }
const onMouseMove = () => {}
const onMouseLeave = () => {}
</script>

<style scoped lang="scss">
.gallery-root {
  display: flex;
  flex-direction: column;
  gap: 12px;
  user-select: none;
}

/* ── 主图 ── */
.main-stage {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: 20px;
  overflow: hidden;
  background: var(--color-background-mute);
  border: 1px solid var(--color-border);
  cursor: zoom-in;

  &:hover .zoom-tip { opacity: 1; }
  &:hover .nav-btn  { opacity: 1; }
}

.main-img {
  width: 100%;
  height: 100%;
  transition: transform 0.4s ease;

  .main-stage:hover & { transform: scale(1.03); }
}

.img-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--el-text-color-placeholder);
  font-size: 13px;
}

/* 放大提示 */
.zoom-tip {
  position: absolute;
  bottom: 14px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 14px;
  border-radius: 20px;
  background: rgba(0,0,0,0.45);
  backdrop-filter: blur(6px);
  color: #fff;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.25s;
  pointer-events: none;
  white-space: nowrap;
}

/* 箭头 */
.nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(8px);
  color: #444;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 12px rgba(0,0,0,0.15);
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 3;

  &:hover { background: #fff; transform: translateY(-50%) scale(1.1); }
  &.nav-prev { left: 12px; }
  &.nav-next { right: 12px; }
}

/* 圆点 */
.dots {
  position: absolute;
  bottom: 14px;
  right: 14px;
  display: flex;
  gap: 5px;
  z-index: 3;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255,255,255,0.5);
  cursor: pointer;
  transition: all 0.2s;

  &.active { background: #fff; width: 18px; border-radius: 4px; }
}

/* ── 缩略图条 ── */
.thumb-strip {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 2px 2px 6px;

  &::-webkit-scrollbar { height: 4px; }
  &::-webkit-scrollbar-thumb { background: var(--el-border-color); border-radius: 4px; }
}

.thumb-item {
  position: relative;
  flex-shrink: 0;
  width: 68px;
  height: 68px;
  border-radius: 10px;
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover { border-color: rgba(102,126,234,0.5); }

  &.active {
    border-color: #667eea;
    box-shadow: 0 0 0 2px rgba(102,126,234,0.25);
  }

  &:not(.active) .thumb-overlay { background: rgba(255,255,255,0.35); }
}

.thumb-img { width: 100%; height: 100%; }

.thumb-overlay {
  position: absolute;
  inset: 0;
  transition: background 0.2s;
}

.thumb-err {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-placeholder);
}

/* 切换动画 */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
