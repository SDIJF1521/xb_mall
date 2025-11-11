<template>
  <BuyerTemplate :currentComponents="['UserListMain']" />
</template>
<script setup lang="ts">
import {ref,onMounted} from 'vue'
import BuyerTemplate from '@/moon/buyer_template.vue'
import UserListMain from '@/views/buyer_user_list_id/content/user_list_main.vue'

defineOptions({
    name: 'BuyerUserListId',
    components: {
        BuyerTemplate,
        UserListMain
    }
})
</script>
