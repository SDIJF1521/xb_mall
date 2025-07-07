<template>
    <ul v-if="mall_apply">
        <li v-for="item in mall_apply">{{ item[0] }}</li>
    </ul>
</template>
<script setup lang="ts">
import {ref,onMounted} from 'vue'
import axios from 'axios';
const Axios = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
  });

const mall_apply = ref([])
onMounted(async() =>{
    
})

</script>
