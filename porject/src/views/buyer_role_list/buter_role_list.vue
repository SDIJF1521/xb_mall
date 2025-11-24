<template>
  <BuyerTemplate :currentComponents="['RoleListMain']"/>
</template>
<script setup lang="ts">
import BuyerTemplate from '@/moon/buyer_template.vue'
import RoleListMain from '@/views/buyer_role_list/content/role_list_main.vue'

defineOptions({
  name: 'BuyerRoleList',
  components: {
    BuyerTemplate,
    RoleListMain,
  },
})
</script>
