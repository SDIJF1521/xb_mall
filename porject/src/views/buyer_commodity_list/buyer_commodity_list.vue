<template>
   <BuyerTemplate :currentComponents="['CommodityList']"/>
</template>

<script setup lang="ts">
import BuyerTemplate from '@/moon/buyer_template.vue'
import CommodityList from '@/views/buyer_commodity_list/content/commodity_list.vue'



defineOptions({
  name: 'BuyerCommodityList',
  components: {
    BuyerTemplate,
    CommodityList,
  },
})
</script>
