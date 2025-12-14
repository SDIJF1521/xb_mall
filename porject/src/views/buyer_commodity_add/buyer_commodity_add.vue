<template>
    <BuyerTemplate :currentComponents="['CommodityAdd']"/>
</template>
<script setup lang="ts">
import axios from 'axios'
import BuyerTemplate from '@/moon/buyer_template.vue'
import {ref,onMounted} from 'vue'
import CommodityAdd from './content/commodity_add.vue'

defineOptions({
    name:'BuyerCommodityAdd',
    components:{
        BuyerTemplate,
        CommodityAdd
    }
})
</script>
