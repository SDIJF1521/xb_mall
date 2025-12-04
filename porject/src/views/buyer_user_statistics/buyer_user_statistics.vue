<template>
  <BuyerTemplate :currentComponents="['RoleRatio']" />
</template>
<script setup lang="ts">
import {ref, onMounted} from 'vue'
import RoleRatio from '@/views/buyer_user_statistics/content/role_ratio.vue'
import BuyerTemplate from '@/moon/buyer_template.vue'
import UserListMain from '@/views/buyer_user_list_id/content/user_list_main.vue'


defineOptions({
    name: "BuyerUserStatistics",
    components: {
        UserListMain,
        BuyerTemplate
    }
})

</script>
