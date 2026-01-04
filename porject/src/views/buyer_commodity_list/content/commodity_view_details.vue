<template>
  <div v-if="commodity" style="padding: 20px;">
    <el-descriptions :column="2" border>
      <el-descriptions-item label="商品ID">{{ commodity.id }}</el-descriptions-item>
      <el-descriptions-item label="商品名称">{{ commodity.name }}</el-descriptions-item>
      <el-descriptions-item label="商品状态">
        <el-tag :type="commodity.audit === 1 ? 'primary' : commodity.audit === 0 ? 'warning' : commodity.audit === 3 ? 'danger' : 'danger'">
          {{ commodity.audit === 1 ? '审核通过' : commodity.audit === 0 ? '待审核' : commodity.audit === 3 ? '已下架' : '审核未通过' }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ commodity.time }}</el-descriptions-item>
      <el-descriptions-item label="分类" :span="2" v-if="commodity.classify_categorize">
        {{ commodity.classify_categorize }}
      </el-descriptions-item>
      <el-descriptions-item label="商品信息" :span="2">
        <div style="white-space: pre-wrap; word-break: break-all;">{{ commodity.info }}</div>
      </el-descriptions-item>
      <el-descriptions-item label="商品类型" :span="2" v-if="commodity.types && commodity.types.length > 0">
        <el-tag v-for="(type, index) in commodity.types" :key="index" style="margin-right: 8px;">
          {{ type }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="商品图片" :span="2" v-if="commodity.img_list && commodity.img_list.length > 0">
        <div class="image-container">
          <div
            v-for="(img, index) in commodity.img_list"
            :key="index"
            class="image-wrapper"
          >
            <el-image
              :src="`data:image/jpeg;base64,${img}`"
              class="commodity-image"
              fit="cover"
              :preview-src-list="commodity.img_list!.map(img => `data:image/jpeg;base64,${img}`)"
              :initial-index="index"
              preview-teleported
            />
          </div>
        </div>
      </el-descriptions-item>
      <el-descriptions-item label="规格列表" :span="2" v-if="commodity.specification_list && commodity.specification_list.length > 0">
        <el-table :data="commodity.specification_list" border style="width: 100%;">
          <el-table-column label="规格组合" width="300">
            <template #default="{ row }">
              <el-tag
                v-for="(spec, index) in row.specs"
                :key="index"
                style="margin-right: 8px;"
                type="info"
                effect="plain"
              >
                {{ spec }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="price" label="价格" width="150">
            <template #default="{ row }">
              ¥{{ row.price }}
            </template>
          </el-table-column>
          <el-table-column prop="stock" label="库存" width="150">
            <template #default="{ row }">
              {{ row.stock }}
            </template>
          </el-table-column>
        </el-table>
      </el-descriptions-item>
    </el-descriptions>
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: 'CommodityViewDetails',
})

interface Commodity {
  id: number
  name: string
  mg_list?: string[]
  img_list?: string[]
  info: string
  specification_list?: any[]
  types?: string[]
  classify_categorize?: string | number
  description?: string
  audit: number
  time: string
}

const props = defineProps<{
  commodity: Commodity | null
}>()
</script>

<style scoped>
.image-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.image-wrapper {
  width: 150px;
  height: 150px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #e4e7ed;
}

.commodity-image {
  width: 100% !important;
  height: 100% !important;
  max-width: 150px !important;
  max-height: 150px !important;
  min-width: 150px !important;
  min-height: 150px !important;
  display: block;
}

.commodity-image :deep(.el-image__wrapper) {
  width: 150px !important;
  height: 150px !important;
  max-width: 150px !important;
  max-height: 150px !important;
}

.commodity-image :deep(.el-image__inner) {
  width: 150px !important;
  height: 150px !important;
  max-width: 150px !important;
  max-height: 150px !important;
  object-fit: cover !important;
  object-position: center !important;
}
</style>

<style>
/* 控制图片预览对话框的尺寸 */
.el-image-viewer__wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.el-image-viewer__canvas {
  max-width: 80vw !important;
  max-height: 80vh !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.el-image-viewer__canvas img {
  max-width: 80vw !important;
  max-height: 80vh !important;
  width: auto !important;
  height: auto !important;
  object-fit: contain !important;
}
</style>

