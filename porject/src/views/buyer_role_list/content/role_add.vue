<template>
    <el-form
    ref="ruleFormRef"
    label-width="auto"
  >
  </el-form>
</template>
<script lang="ts" setup>
import axios from 'axios'
import { useRoute } from 'vue-router'
import {ref,onMounted} from 'vue'

defineOptions({
  name: 'RoleAdd'
})

const token = ref(localStorage.getItem('buyer_access_token')||'')
const route = useRoute().params
const mall_id = ref(route.id)


</script>
