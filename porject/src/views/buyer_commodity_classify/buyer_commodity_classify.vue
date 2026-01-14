<template>
  <BuyerTemplate :currentComponents="['CommodityClassify']" />
</template>

<script setup lang="ts">
import BuyerTemplate from '@/moon/buyer_template.vue'
import CommodityClassify from '@/views/buyer_commodity_classify/content/commodity_classify.vue'

defineOptions({
  name: 'BuyerCommodityClassify',
  components: {
    BuyerTemplate,
    CommodityClassify,
  },
})
</script>
 