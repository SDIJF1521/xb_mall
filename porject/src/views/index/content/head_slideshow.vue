<template>
  <el-carousel :interval="4000" type="card" height="220px" v-if="banners.length > 0">
    <el-carousel-item v-for="item in banners" :key="item.id" @click="goToCommodity(item)">
      <div class="banner-item">
        <img
          :src="item.img.startsWith('data:') ? item.img : 'data:image/jpeg;base64,' + item.img"
          :alt="item.title"
          class="banner-img"
        />
        <div class="banner-overlay">
          <span class="banner-title">{{ item.title }}</span>
          <span class="banner-shop">{{ item.mall_name }}</span>
        </div>
      </div>
    </el-carousel-item>
  </el-carousel>
  <el-carousel :interval="4000" type="card" height="220px" v-else>
    <el-carousel-item v-for="i in 4" :key="i">
      <div class="banner-placeholder">
        <span>广告位招租</span>
      </div>
    </el-carousel-item>
  </el-carousel>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

defineOptions({ name: 'HeadSlideshow' })

const router = useRouter()

interface BannerAd {
  id: number
  mall_id: number
  shopping_id: number
  title: string
  img: string
  mall_name: string
  commodity_name: string
}

const banners = ref<BannerAd[]>([])

async function loadBanners() {
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/ad_banner_active')
    if (data.current && Array.isArray(data.data)) {
      banners.value = data.data.filter((b: BannerAd) => b.img)
    }
  } catch {
    // 加载失败静默处理，显示占位
  }
}

function goToCommodity(item: BannerAd) {
  router.push(`/commodity/${item.mall_id}/${item.shopping_id}`)
}

onMounted(() => {
  loadBanners()
})
</script>

<style scoped>
.banner-item {
  width: 100%;
  height: 100%;
  position: relative;
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
}

.banner-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.banner-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 10px 14px;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.6));
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.banner-title {
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 70%;
}

.banner-shop {
  color: rgba(255, 255, 255, 0.85);
  font-size: 12px;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}

.banner-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #475669;
  opacity: 0.6;
  border-radius: 8px;
}

.el-carousel__item:nth-child(2n) .banner-placeholder {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: rgba(255, 255, 255, 0.7);
}

.el-carousel__item:nth-child(2n + 1) .banner-placeholder {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: rgba(255, 255, 255, 0.7);
}

:deep(.el-carousel__item) {
  border-radius: 8px;
  overflow: hidden;
}
</style>
